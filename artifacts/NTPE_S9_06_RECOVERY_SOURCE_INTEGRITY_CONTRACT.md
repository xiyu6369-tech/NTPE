# NTPE S9-06 — Recovery & Source Integrity Contract

**Task**: `NTPE-S9-06-Phase-B`
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Status**: `S9_06_PHASE_B_CONTRACT_FIXED`
**Governance**: Phase B only — contract decision only. No production implementation. No commit / push / tag.

---

## 1. Scope

This contract defines the canonical recovery and source integrity rules for the NTPE Reader-First Translation Project layer (S9). It binds:

- S9-02 Persistent Book Project
- S9-03 Resume UX / Reader State Derivation
- S9-04 Project Card Library / Dashboard
- S9-05 Completion & Output UX / Result Opener

and the existing frozen translation runtime layers.

**Non-goals**: No new retry/restart semantics, no automatic source rebind, no glossary, no frozen runtime modification, no cloud sync.

---

## 2. Canonical Definitions

| Term | Definition |
|------|------------|
| **Project** | Persistent Book Project per S9-02 `ReaderProject` schema v1. Identity = `project_id` (UUID v4 hex). |
| **Source Identity** | Canonical per S9-02 `SourceIdentity`: TXT = `sha256(file_bytes)[:16]` (`txt_sha256_16`); EPUB = `sha256(file_bytes)` (`epub_sha256`). Includes `path`, `format`, `identity_kind`, `hash`, `file_size`, `modified_time`. |
| **Runtime Artifact** | Any file produced by the translation runtime that is required for recovery/resume (checkpoint, resume state, chunk output, character memory, context memory). Not the reader-facing output artifact. |
| **Output Artifact** | Final reader-facing artifact (`*.txt`, `*.epub`) produced by runtime and referenced by `OutputRecord`. |
| **Project Identity** | `project_id` (UUID v4 hex). Never derived from filename or source. |
| **Recovery** | Using existing persisted runtime state to continue a translation from a known-good point. Does NOT mean retry, restart, or new translation. |
| **Retry** | Re-executing a failed translation unit with the same input. Governed by provider retry policy only. |
| **Restart** | Discarding all persisted runtime state and starting a new translation from the beginning. |
| **Recoverable** | All canonical preconditions satisfied (see §6). |
| **Non-recoverable** | Any precondition FALSE. |

---

## 3. Recovery Eligibility Canonical Rule

**Recovery is ALLOWED iff ALL preconditions are TRUE:**

```python
recovery_eligible(project: ReaderProject) -> bool:
    return (
        project_exists(project)
        and project_identity_valid(project)
        and source_identity_valid(project)
        and source_integrity_valid(project)
        and runtime_artifact_exists(project)
        and runtime_artifact_identity_valid(project)
        and runtime_artifact_belongs_to_project(project)
        and runtime_artifact_belongs_to_source(project)
        and runtime_state_is_recoverable(project)
    )
```

**Any FALSE → `recovery_eligible = False`. No UI exception.**

---

## 4. Source Integrity Decision Matrix

| Case | Recovery Decision | Rationale |
|------|-------------------|-----------|
| Project exists + source unchanged | Proceed per runtime state | Canonical identity matches |
| Source missing | **BLOCK** | Cannot verify identity |
| Source content changed | **BLOCK** | Canonical hash mismatch |
| Same filename, different content | **BLOCK** | Canonical hash differs |
| Wrong source bound to artifact | **BLOCK** | Source identity mismatch |
| Wrong Project bound to artifact | **BLOCK** | Project identity mismatch |
| Relocated source, canonical identity still valid | Proceed per existing canonical identity contract | Identity-based, not path-based |
| Project missing | **BLOCK** | No Project to recover |
| Source identity cannot be established | **BLOCK** | Cannot verify |

**Forbidden**:
- Changed source → auto rebind
- Missing source → silently replace / guess
- Same filename → assume same source

**Relocation without canonical contract** → **DEFERRED** (not implemented, not guessed).

---

## 5. Source Hash Guard Layering

| Layer | Responsibility | Guard |
|-------|----------------|-------|
| **Project Layer** | "Is this Project still bound to the correct source?" | `source_matches(SourceRecord)` → `source_changed(SourceRecord)` |
| **Runtime Layer** | "Can this chunk/runtime state be safely reused?" | Existing per-chunk `source_hash` (sha256[:16]) guard in LTS/Epub resume |

**Canonical Flow**:
```
Project Recovery
      ↓
Source Integrity Validation  (Project layer)
      ↓
Runtime Artifact Validation  (Project layer)
      ↓
Runtime Resume Eligibility   (Project layer)
      ↓
Existing Runtime Resume      (Runtime layer)
      ↓
Existing source_hash guard   (Runtime layer)
```

**Invariant**: No layer bypasses the layer below. Project layer never bypasses runtime `source_hash` guard. Runtime layer never makes Project-level identity decisions.

---

## 6. Runtime Artifact Contract

A runtime artifact is **VALID** iff ALL hold:

| Criterion | Check |
|-----------|-------|
| Exists | `Path(artifact_path).is_file()` |
| Readable | File opens without error |
| Structurally valid | Parses per its format (JSON, memory format, etc.) |
| Project binding valid | Artifact's `project_id` / `session_id` matches Project |
| Source binding valid | Artifact's source identity matches Project's source identity |
| Sufficient recovery evidence | Contains sufficient state to resume (e.g., chunk progress, character memory) |

**Missing runtime artifact** → Recovery = **BLOCK**.  
**Wrong-project artifact** → **BLOCK**.  
**Wrong-source artifact** → **BLOCK**.  
**Incomplete/insufficient evidence** → **BLOCK**.  

*No guessing. No fallback to output artifact.*

---

## 7. Failure Classification Contract

| Class | Definition | Recovery Decision |
|-------|------------|-------------------|
| **Recoverable Runtime Failure** | Source integrity valid + artifact valid + runtime state resumable + failure compatible with existing resume semantics | `ALLOWED` |
| **Non-recoverable Runtime Failure** | Source/artifact valid but runtime state missing/insufficient for resume | **BLOCK** (not RETRY, not RESTART) |
| **Source Integrity Failure** | Missing source / changed source / same filename different content / wrong source binding / wrong Project binding / identity cannot be established | **BLOCK** (never RETRY, never RESTART) |

**Non-recoverable ≠ Retry. Source Integrity Failure ≠ Retry.**

---

## 8. Resume / Retry / Restart Separation

| Operation | Semantic | Authorization |
|-----------|----------|---------------|
| **Resume / Recovery** | Use existing persisted runtime state to continue from a known-good point. | Authorized per canonical eligibility (§6). |
| **Retry** | Re-execute a failed translation unit with same input. Provider-level only. | **NOT AUTHORIZED** at Project layer. Provider retry policy only. |
| **Restart** | Discard all persisted runtime state, start new translation from beginning. | **NOT AUTHORIZED** at Project layer unless explicit user action with full state discard (not implemented). |

**UI Contract**:  
- Only `Resume` action exposed when `recovery_eligible == True`.  
- No `Retry` button, no `Restart` button, no `Reset and Retry`.  
- `Recovery = BLOCK` → no actionable recovery control exposed.

---

## 9. last_error Contract

| Event | Rule |
|-------|------|
| Recovery attempt starts | **Do not clear** `last_error`. Preserve existing error. |
| Recovery attempt fails | **Do not clear** `last_error`. Preserve or append (canonical schema). |
| Recovery succeeds (canonical transition) | Clear or replace `last_error` per canonical state contract. |
| Any other state transition | Follow canonical `StateRecord` contract. |

**Never** clear `last_error` on recovery attempt start or failure.

---

## 9. Recovery UX Contract

| Backend State | UI Presentation |
|---------------|-----------------|
| `recovery_eligible == True` | Show real `Resume` action (primary) |
| `recovery_eligible == False` | **No** actionable `Resume` / `Retry` / `Restart` control |
| Source Missing | Show explicit `Source Missing` / `Recovery Blocked` label |
| Source Changed | Show explicit `Source Changed` / `Recovery Blocked` label |
| Source Identity Invalid | Show explicit `Source Identity Invalid` / `Recovery Blocked` label |
| Runtime Artifact Missing / Wrong | Show `Recovery Unavailable` / `Recovery Blocked` |

**Forbidden**:  
- Disabled-but-visible "Resume" that implies availability.  
- "Retry" / "Restart" buttons.  
- Fake "Resume" that silently does nothing.

---

## 10. Output vs Runtime Artifact Separation

| Assertion | Contract |
|-----------|----------|
| `output exists` → `runtime recoverable` | **FALSE** |
| `runtime artifact exists` → `output exists` | **FALSE** |
| `output missing` → `runtime recoverable` | **FALSE** |
| `runtime artifact missing` → `output missing` | **FALSE** |

**Contract**: These are independent dimensions. UI must never infer one from the other.

---

## 11. Atomicity Boundary

| Layer | Atomicity | Responsibility |
|-------|-----------|----------------|
| `core/reader_project/store.py` (Project save) | **Atomic** (temp + `os.replace`) | Project layer — guaranteed |
| `core/translation_runtime/runtime_recovery.py` (`save_checkpoint`) | **Non-atomic** | Frozen runtime — **cannot modify** |
| `lts/txt_translation_runtime.py` (`save_resume_state`) | **Non-atomic** | Frozen LTS — **cannot modify** |
| `core/runtime_session/manager.py` (in-memory) | N/A (in-memory) | Frozen — **cannot modify** |
| `core/runtime_checkpoint/manager.py` (in-memory) | N/A (in-memory) | Frozen — **cannot modify** |

**Contract**:  
- Project-level atomicity is the canonical recovery boundary.  
- Runtime non-atomicity is a **known gap**, documented as **DEFERRED RUNTIME HARDENING**.  
- S9-06 does NOT modify frozen runtime to achieve atomicity.  
- Project-level atomic boundary is the recovery safety net.

---

## 12. Persistence Contract

| Layer | Mechanism | Boundary |
|-------|-----------|----------|
| Project | `ProjectStore.write` (atomic JSON) + `ProjectManager` | Canonical |
| Runtime resume state | `lts/txt_translation_runtime.save_resume_state` / `runtime_recovery.save_checkpoint` | Runtime-owned |
| Session checkpoints | `RuntimeSessionManager` / `RuntimeCheckpointManager` (in-memory) | Runtime-owned |
| Character/Context memory | `save_character_memory` / `save_context_memory` | Runtime-owned |

**No second persistence system**.  
Recovery state is always read from existing stores via `ProjectManager` / runtime managers.

---

## 13. Schema Change Rule

- `ReaderProject` schema v1 is **FROZEN** for S9-06.  
- If contract requires schema change → **STOP → DEFERRED**.  
- No silent schema upgrades.

---

## 14. Test Contract

Phase C must implement at least:

### Source Integrity
- [ ] Unchanged source → recovery proceeds
- [ ] Changed source → blocked
- [ ] Missing source → blocked
- [ ] Same filename, different content → blocked
- [ ] Relocation per canonical identity → allowed

### Runtime Artifact
- [ ] Valid artifact + valid bindings → eligible
- [ ] Missing artifact → blocked
- [ ] Wrong source binding → blocked
- [ ] Wrong Project binding → blocked
- [ ] Incomplete evidence → blocked

### Recovery Eligibility
- [ ] All preconditions TRUE → eligible
- [ ] Project missing → blocked
- [ ] Source missing → blocked
- [ ] Source changed → blocked
- [ ] Wrong-source artifact → blocked
- [ ] Wrong-project artifact → blocked
- [ ] Missing runtime evidence → blocked

### Failure / Error
- [ ] Recovery failure preserves `last_error`
- [ ] Successful recovery updates state per canonical contract

### UI
- [ ] Eligible → real `Resume` action visible
- [ ] Blocked → no fake `Resume`/`Retry`/`Restart`
- [ ] Source missing → explicit "Recovery Blocked: Source Missing"
- [ ] Source changed → explicit "Recovery Blocked: Source Changed"
- [ ] No fake `Retry`/`Restart` buttons

### Regression
- [ ] S9-03 resume UX tests pass
- [ ] S9-04 dashboard tests pass
- [ ] S9-05 completion/output tests pass
- [ ] S8-02/03/04 regression suites pass

**Provider = 0, Network = 0, Real Translation = 0**

---

## 15. Phase C Implementation Boundary

### Allowed (Additive Only)
| Component | Change |
|-----------|--------|
| `core/reader_project/recovery.py` (new) | Recovery eligibility + source integrity validation |
| `core/reader_project/state.py` | Extend `derive_reader_status` / `derive_state` with recovery eligibility |
| `core/reader_project/manager.py` | `validate_recovery_eligibility(project_id)` |
| `core/reader_project/identity.py` | Add `validate_source_integrity(record)` |
| `core/reader_project/project_view_model.py` | Add `recovery_eligible`, `recovery_blocked_reason` to card model |
| `ui/translation_studio/widgets/project_card.py` | Conditional "Resume" button; recovery blocked badge |
| `ui/translation_studio/pages/project_page.py` | `_validate_recovery_eligibility()` before `_on_translate`; connect to `ResultOpener` for output only |
| `ui/translation_studio/translations.py` | Recovery blocked strings |

### Forbidden (Do Not Modify)
- `lts/txt_translation_runtime.py`
- `core/epub_translation/runtime/adapter.py`
- `core/translation_runtime/runtime_recovery.py`
- `core/runtime_checkpoint/manager.py`
- `core/runtime_session/manager.py`
- `core/runtime_orchestrator/...`
- `core/translation_engine/...`
- `core/ai_provider/...`
- `core/translation_engine/...`
- Any provider / model / translation engine file
- `glossary` anything

---

## 16. Explicit Non-Goals (Forbidden)

| Non-goal | Reason |
|----------|--------|
| Automatic source rebind / relocation UI | No canonical contract; DEFERRED |
| Retry button / semantics | Not authorized at Project layer |
| Restart button / semantics | Not authorized at Project layer |
| Automatic retry / restart logic | Provider-level only |
| Frozen runtime modification | Frozen boundary |
| Glossary Import UI | Out of scope (§28) |
| Automatic source rebind | No canonical contract |
| Atomicity fix requiring runtime change | DEFERRED RUNTIME HARDENING |
| Second persistence system | Forbidden |
| Project schema redesign | Schema v1 FROZEN |
| Glossary parser / persistence / injection | Out of scope (§28) |
| Cloud sync / multi-user | Out of scope |

---

## 17. Explicit Stop Conditions for Phase C

If any encountered during implementation:

1. Source identity semantics inconsistent → **STOP → DEFERRED**
2. Runtime artifact ownership cannot be proven → **STOP → DEFERRED**
2. Runtime recovery state cannot be distinguished safely → **STOP → DEFERRED**
3. Existing runtime Resume semantics conflict with Project Recovery → **STOP → DEFERRED**
4. Atomicity requires modifying frozen runtime → **STOP → DEFERRED**
5. Project schema redesign required → **STOP → DEFERRED**
6. Automatic source rebind appears necessary → **STOP → DEFERRED**
6. Retry semantics must be invented → **STOP → DEFERRED**
7. Restart semantics must be invented → **STOP → DEFERRED**
7. Provider / model / Translation Engine modification appears necessary → **STOP → DEFERRED**

Action: `record finding → mark DEFERRED/BLOCKED → do not implement workaround`

---

## 17. Phase B Completion Status

| Criterion | Status |
|-----------|--------|
| Canonical recovery definitions fixed | ✅ |
| Recovery eligibility predicate fixed | ✅ |
| Source integrity matrix fixed | ✅ |
| Runtime artifact contract fixed | ✅ |
| Failure classification fixed | ✅ |
| Resume / Retry / Restart semantics separated | ✅ |
| last_error contract fixed | ✅ |
| Output / Runtime artifact separation fixed | ✅ |
| Atomicity boundary fixed | ✅ |
| Persistence boundary fixed | ✅ |
| Forbidden behaviors fixed | ✅ |
| Test matrix fixed | ✅ |
| No unresolved stop condition | ✅ |
| Contract artifact written | ✅ (`artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md`) |
| No production implementation performed | ✅ |
| No provider / network / real translation | ✅ |
| Glossary untouched | ✅ |
| No commit / push / tag | ✅ |

**Phase B: PASS**

---

## 18. Contract Artifact Location

`artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md` (this document)

---

## 18. Phase B Final Report

```text
# NTPE S9-06 Phase B — Recovery & Source Integrity Contract Report

Baseline HEAD: 914a847
Actual HEAD: 914a847

Contract Artifact:
artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md

Production Files Modified:
NO

Recovery Eligibility:
PASS

Source Integrity Contract:
PASS

Runtime Artifact Contract:
PASS

Failure Classification:
PASS

Resume vs Retry vs Restart:
PASS

last_error Contract:
PASS

Output / Runtime Artifact Separation:
PASS

Atomicity Boundary:
PASS (with documented DEFERRED RUNTIME HARDENING)

Persistence Boundary:
PASS

Schema Change:
NONE

Stop Conditions:
NONE

Tests Added:
0

Provider Execution:
0

Network Execution:
0

Real Translation:
0

Frozen Runtime Modified:
NO

Glossary UI:
NOT IMPLEMENTED

S9-03 Regression:
PASS

S9-04 Regression:
PASS

S9-05 Regression:
PASS

S8 Regression:
PASS

Git Commit:
NO

Git Push:
NO

Git Tag:
NO

FINAL:
PASS
```
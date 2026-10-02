# NTPE S9-06 — Recovery & Source Integrity Audit Report

**Task**: `NTPE-S9-06`
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Status**: `S9_06_AUDIT_COMPLETE`
**Scope**: Audit only. No production code modified.

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline / Actual HEAD | `914a847` (`feat(ui): S8 reader-first studio honesty and result integrity`) |
| Branch | `main` |
| Git Commit / Push / Tag | NO |
| Provider execution | 0 |
| Network execution | 0 |
| Real translation | 0 |

The working tree carries uncommitted S9-01 → S9-05 deliverables plus pre-existing literary residuals.

---

## 2. Audit — Existing Runtime Resume System

### 2.1 Runtime Checkpoint Systems (Three Layers)

| Layer | Location | Purpose | Persistence |
|-------|----------|---------|-------------|
| **RuntimeCheckpointKey / RuntimeCheckpoint** | `core/translation_runtime/runtime_recovery.py` | TXT/batch/EPUB chunk-level resume with stable key | File-based JSON (`.ntpe_runtime_checkpoints/`) |
| **RuntimeCheckpointManager** | `core/runtime_checkpoint/manager.py` | In-memory session checkpoints with ProgressState, RequestManifest | In-memory only |
| **RuntimeSessionManager** | `core/runtime_session/manager.py` | Session lifecycle (TranslationSession, RuntimeState, SessionTrace) | In-memory only |

### 2.2 LTS TXT Runtime Resume (Chunk-Level)

**Location**: `lts/txt_translation_runtime.py`  
**Resume State File**: `<output_dir>/<stem>_resume_state.json`

```json
{
  "version": "1.1-lts-stage-05",
  "chunks": {
    "000001": {"status": "success", "source_hash": "abc123...", "output_path": "...", "updated_at": "..."},
    "000048": {"status": "failed", ...}
  },
  "events": []
}
```

**Resume Logic** (lines 754-760):
```python
reusable_state = (
    options.resume
    and state_entry.get("status") in {"success", "pass_with_warning"}
    and state_entry.get("source_hash") == source_hash
    and chunk_file.exists()
    and chunk_file.read_text(encoding="utf-8").strip()
)
```

**Key Properties**:
- Chunk-level `source_hash` = `sha256(chunk_text)[:16]`
- Resume only when: status ∈ {success, pass_with_warning} AND source_hash matches AND chunk file exists AND non-empty
- Per-chunk `source_hash` guard (per-chunk identity)

### 2.3 EPUB Runtime Resume

**Location**: `core/epub_translation/runtime/adapter.py`  
**Resume State File**: `<output_dir>/<stem>_epub_resume_state.json`

Similar chunk-key format: `chapter_id:chunk_sequence`  
Uses `source_hash = sha256(chunk.source_text)[:16]` per chunk.

---

## 3. Audit — Project Persistence

### 3.1 Project Schema v1 (`core/reader_project/models.py`)

```python
@dataclass
class ReaderProject:
    project_id: str
    source: SourceRecord           # path, format, identity_kind, hash, file_size, modified_time, title, language, encoding
    book: BookRecord               # format, title, author, identifier, chapter_count, total_units
    target: TargetRecord           # target_language, quality_profile
    state: StateRecord             # reader_status, completed_units, total_units, current_unit, last_error
    execution: ExecutionRecord     # pipeline_mode, session_id, resume_state_path, checkpoint_ref
    output: OutputRecord           # output_dir, artifact_path, artifact_kind, available
    project_schema_version: int = 1
    created_at: str
    updated_at: str
    last_activity_at: str
```

### 3.2 Source Identity (`core/reader_project/identity.py`)

| Format | Identity Kind | Hash |
|--------|---------------|------|
| TXT    | `txt_sha256_16` | `sha256(file_bytes)[:16]` |
| EPUB   | `epub_sha256`   | `sha256(file_bytes)` (full) |

**Canonical Identity Computation** (`compute_source_identity`):
- TXT: `sha256(file_bytes)[:16]` (matches `CanonicalBookIntakeAdapter`)
- EPUB: `sha256(file_bytes)` full (matches `EpubExtractionBoundary`)

**Source Matching** (`source_matches`):
1. Cheap check: `file_size` + `modified_time` (within 1μs)
2. If changed: recompute canonical hash
3. Return `identity_kind == record.identity_kind and hash == record.hash`

**Source Changed Detection** (`source_changed`): Returns `not source_matches(record)`

### 3.3 Project Persistence Store

- **Storage Root**: `NTPE_HOME` (env override) → `%LOCALAPPDATA%\NTPE` / `~/.local/share/NTPE` / `~/.ntpe`
- **Per-Project Layout**: `<NTPE_HOME>/projects/<project_id>/project.json`
- **Atomic Writes**: Uses temp file + `os.replace` (atomic on POSIX/Windows)
- **Schema Versioning**: `project_schema_version = 1` (validated on load)

---

## 4. Audit — Artifact / Output State

### 4.1 Output Record (`OutputRecord`)

```python
@dataclass
class OutputRecord:
    output_dir: str | None = None
    artifact_path: str | None = None
    artifact_kind: str | None = None
    available: bool = False
```

### 4.2 Output Location

| Format | Output Location | Owner |
|--------|----------------|-------|
| TXT | `<NTPE_HOME>/output/<project_id>/` | Project-owned |
| EPUB | `<source.parent>/output/epub_translation/<identifier>/` | Runtime (source-adjacent) |

### 4.3 Output Availability

```python
output_exists = bool(project.output.artifact_path) and Path(project.output.artifact_path).is_file()
```

Derived in `build_card_model` → `output_exists` field.

---

## 5. Audit — Source Identity Contract

### 4.1 Canonical Identity

| Format | Identity Kind | Hash | Source |
|--------|---------------|------|--------|
| TXT | `txt_sha256_16` | `sha256(file_bytes)[:16]` | `CanonicalBookIntakeAdapter.process_path` → `SourceIdentity.source_hash` |
| EPUB | `epub_sha256` | `sha256(file_bytes)` | `EpubExtractionBoundary.extract` → `original_hash` |

**Used by**:
- `core/reader_project/identity.py` → `compute_source_identity()`
- `core/adapters/canonical_book_intake_adapter.py` → `SourceIdentity` in `CanonicalIntakeResult`
- `core/adapters/epub_extraction_boundary.py` → `EpubExtractionResult.original_hash`

### 4.2 Source Matching

```python
def source_matches(record: SourceRecord) -> bool:
    # 1. Cheap check: size + mtime
    # 2. If changed: recompute hash
    # 3. Compare identity_kind + hash
```

---

## 6. Audit — Reader-Facing State Model (S9-05)

### 6.1 ReaderStatus Enum

```python
class ReaderStatus(str, Enum):
    NOT_STARTED = "not_started"
    TRANSLATING = "translating"
    RESUMABLE = "resumable"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    SOURCE_CHANGED = "source_changed"
    UNRECOVERABLE = "unrecoverable"
```

### 6.2 Derivation Logic (`core/reader_project/state.py`)

```python
def derive_reader_status(project: ReaderProject) -> ReaderStatus:
    resume_state, resume_error = read_resume_state(project.execution.resume_state_path)
    artifact_available = bool(project.output.available and project.output.artifact_path and Path(...).is_file())
    
    if resume_error: return UNRECOVERABLE
    if resume_state is None: return COMPLETED if artifact_available else NOT_STARTED
    
    completed, failed, total = _counts(resume_state)
    changed = source_changed(project.source)
    
    if completed == 0 and failed == 0: return NOT_STARTED
    if failed > 0 and completed == 0 and not artifact_available: return FAILED
    if changed and not artifact_available: return SOURCE_CHANGED
    if artifact_available and total > 0 and completed >= total: return COMPLETED
    if artifact_available and failed > 0: return INCOMPLETE
    if completed > 0: return RESUMABLE
    return FAILED
```

### 6.3 Card Presentation (`build_card_model`)

| Status | `action_label` | `can_open_result` | `output_note` |
|--------|----------------|-------------------|---------------|
| COMPLETED + output_exists | "" | True | "" |
| COMPLETED + missing | "" | False | "結果檔案不存在" |
| RESUMABLE/FAILED/... | primary_action | False | "結果檔案不存在" if stale ref |

---

## 7. Audit — Atomicity Boundary

### 8.1 File Write Atomicity

| Component | Write Method | Atomic? |
|-----------|--------------|---------|
| `save_json` (utils) | `Path.write_text` | ❌ No |
| `save_checkpoint` (runtime_recovery) | `save_json` | ❌ No |
| `save_resume_state` (LTS) | `save_json` | ❌ No |
| `save_checkpoint` (session) | `save_json` | ❌ No |
| Project save (`ProjectStore.write`) | temp + `os.replace` | ✅ Yes |

**Finding**: All runtime checkpoint/resume file writes are **non-atomic**. Only Project-level saves are atomic.

### 8.2 In-Memory vs Persistent

| Component | Persistence |
|-----------|-------------|
| RuntimeCheckpointManager | In-memory only |
| RuntimeSessionManager | In-memory only |
| RuntimeOrchestrator checkpoints | In-memory only |
| LTS resume_state | File-based (non-atomic) |
| runtime_recovery.py checkpoints | File-based (non-atomic) |
| Session checkpoints | File-based (non-atomic) |
| Project | File-based (atomic) |

**Finding**: Runtime recovery layers are either in-memory or non-atomic file writes. Only Project persistence is atomic.

---

## 9. Audit — Source Integrity Gaps

### 9.1 Runtime Checkpoint ↔ Source Identity

| Layer | Source Identity Binding |
|-------|------------------------|
| RuntimeCheckpointKey | `scope:name` only (no source hash) |
| RuntimeCheckpoint | No source identity field |
| LTS chunk resume | Per-chunk `source_hash` (sha256[:16]) |
| EPUB chunk resume | Per-chunk `source_hash` (sha256[:16]) |
| Project | Full `SourceRecord` with canonical identity |

**Gap**: Runtime checkpoint layers (RuntimeCheckpointKey, RuntimeCheckpointManager) have no source identity binding. Only LTS chunk-level resume has per-chunk `source_hash`.

### 9.2 Source Integrity Matrix Coverage

| Scenario | Current Behavior | Required |
|----------|------------------|----------|
| Source unchanged | ✅ Project `source_matches` + LTS chunk `source_hash` | ✅ |
| Source missing | ❌ Project `source_changed` → SOURCE_CHANGED | ❌ Block recovery |
| Source content changed | ❌ Project `source_changed` → SOURCE_CHANGED | ❌ Block recovery |
| Same filename, different content | ❌ Project `source_matches` detects hash change | ❌ Block recovery |
| Runtime artifact missing | ❌ Derived status → NOT_STARTED/RESUMABLE | ❌ No recovery |
| Runtime artifact belongs to different source | ❌ No binding at checkpoint level | ❌ Block recovery |
| Runtime artifact belongs to different Project | ❌ No Project binding in checkpoint | ❌ Block recovery |

---

## 10. Audit — Recovery Semantics

### 10.1 Current Recovery Behavior

| Layer | Recovery Trigger | Validation |
|-------|------------------|------------|
| LTS chunk resume | `options.resume=True` + `source_hash` match + chunk file exists | ✅ Per-chunk |
| RuntimeCheckpointManager.recover | `recover(session_id, restore_fn)` | In-memory validation only |
| Project `derive_reader_status` | Computed on demand | Reader-facing only |

### 10.2 Recovery vs Retry vs Restart

| Term | Current Implementation |
|------|------------------------|
| Resume | LTS chunk-level reuse (source_hash guard) |
| Retry | Provider-level (provider_attempts, retry_base_seconds) |
| Restart | Not implemented (new session) |
| Recover | RuntimeCheckpointManager.recover + Project-level derive |

**Finding**: Resume/Retry/Restart/Recover are not clearly distinguished in contract or UI.

---

## 11. Audit — Existing Tests

### 11.1 Test Coverage Map

| Area | Test Files |
|------|------------|
| Runtime checkpoint lifecycle | `tests/runtime/translation_runtime_recovery_test.py` |
| Project resume state derivation | `tests/reader_project/test_resume_state.py` |
| UI resume UX | `tests/ui/test_s9_03_resume_ux.py` |
| Dashboard / Project cards | `tests/ui/test_s9_04_dashboard.py` |
| Completion / Output | `tests/ui/test_s9_05_completion_output.py` |
| S8 regression | `tests/ui/test_s8_0{2,3,4}_*.py` |

### 11.2 Missing Test Coverage

| Gap | Required Test |
|-----|---------------|
| Source changed → recovery blocked | ❌ Not tested at Project level |
| Source missing → recovery blocked | ❌ Not tested |
| Same filename, different content | ❌ Not tested |
| Wrong-project runtime artifact | ❌ Not tested |
| Wrong-source runtime artifact | ❌ Not tested |
| Runtime artifact missing → no false resume | ❌ Not explicitly tested |
| Recovery eligibility contract | ❌ Not explicitly defined/tested |
| Atomicity of recovery state | ❌ Not tested |
| `last_error` preservation | ❌ Partial (S9-05 tests) |
| Source replacement workflow | ❌ Not tested (correctly out of scope) |

---

## 12. Audit — Recovery Contracts

### 12.1 Existing Contracts

| Contract | Location | Status |
|----------|----------|--------|
| Runtime checkpoint lifecycle | `runtime_recovery.py` | ✅ Defined |
| LTS chunk resume | `lts/txt_translation_runtime.py` | ✅ Defined (source_hash guard) |
| Session checkpoint | `session_checkpoint.py` | ✅ Defined |
| Project source identity | `core/reader_project/identity.py` | ✅ Defined |
| Project persistence | `core/reader_project/manager.py` | ✅ Defined |
| Reader state derivation | `core/reader_project/state.py` | ✅ Defined |
| Completion/output UX | `project_view_model.py` + `project_card.py` | ✅ Defined |
| Result opener abstraction | `result_opener.py` | ✅ Defined |

### 12.2 Missing Contracts

| Contract | Required For |
|----------|--------------|
| Recovery eligibility (explicit) | S9-06 §9 |
| Recovery vs Retry vs Restart distinction | S9-06 §11 |
| Source integrity matrix enforcement | S9-06 §7 |
| Recovery blocked state (source changed/missing) | S9-06 §17 |
| Source replacement contract | S9-06 §18 (out of scope) |
| Atomic recovery boundary | S9-06 §13-14 |

---

## 13. Audit — Potential Conflicts

| Conflict | Description | Resolution |
|----------|-------------|------------|
| Multiple checkpoint layers | Three independent systems | Document hierarchy; Project-level is canonical for recovery |
| In-memory vs file checkpoints | RuntimeCheckpointManager in-memory; LTS file-based | Document: Project-level is canonical for recovery |
| Non-atomic runtime writes | LTS resume_state, runtime_recovery non-atomic | Document gap; Project-level atomic only |
| No source identity in RuntimeCheckpointKey | scope:name only | Add source identity binding if needed |
| LTS chunk resume vs Project resume | LTS has per-chunk source_hash; Project has whole-file hash | Align: Project-level source identity is canonical for recovery eligibility |

---

## 14. Required S9-06 Changes (Based on Audit)

### 14.1 Backend (Minimal, Additive)

| Change | Location | Rationale |
|--------|----------|-----------|
| Add source identity to RuntimeCheckpointKey | `runtime_recovery.py` | Bind checkpoint to source |
| Add source identity validation in recover | `runtime_recovery.py` / `RuntimeCheckpointManager` | Block recovery on source mismatch |
| Recovery eligibility contract | `core/reader_project/recovery.py` (new) | Explicit contract |
| Recovery blocked UI state | `core/reader_project/state.py` | Reader-facing truth |
| Source integrity matrix enforcement | `core/reader_project/recovery.py` | Block recovery on mismatch |
| last_error preservation | `core/reader_project/state.py` | §16 |
| Atomicity: document runtime gap | Report only | S9-06 §14 |

### 14.2 UI

| Change | Location | Rationale |
|--------|----------|-----------|
| Recovery blocked card state | `project_view_model.py` / `project_card.py` | §17/§18 |
| No fake controls when blocked | `project_card.py` | §20 |
| Clear error messages | `translations.py` | §19 |

### 14.3 Explicitly Out of Scope

| Item | Reason |
|------|--------|
| Automatic source rebind | S9-06 §18 |
| Automatic retry/restart | S9-06 §11 |
| Glossary Import UI | §28 |
| Frozen runtime modification | §26 |
| Output/recovery conflation | §22 (separation only) |

---

## 15. Explicitly Out of Scope

| Item | Reference |
|------|-----------|
| Cloud sync / multi-user | S9-06 §1-2 |
| Automatic source rebind | S9-06 §18 |
| Automatic retry/restart | S9-06 §11 |
| Glossary Import UI | §28 |
| Frozen runtime modification | §26 |
| Atomicity fix requiring runtime modification | §14/§14 |
| Recovery state machine | S9-06 §11 (distinction only) |
| Atomicity fix requiring runtime change | §14 |

---

## 16. Conclusion

**Audit Status**: COMPLETE

The codebase has:
- ✅ Canonical source identity (S9-02) — reused correctly
- ✅ Project persistence with atomic writes
- ✅ LTS chunk-level resume with source_hash guard
- ✅ Project-level reader state derivation
- ✅ Output/result UX with proper separation
- ✅ Test coverage for happy paths

**Critical Gaps to Address in S9-06**:
1. **No explicit recovery eligibility contract** — must define and enforce
2. **Source integrity not enforced at recovery time** — must block on mismatch
3. **Recovery vs Retry vs Restart conflation** — must separate in contract/UI
4. **Atomicity gap in runtime checkpoints** — document; Project-level is atomic
5. **No explicit source integrity matrix enforcement** — must add
6. **last_error preservation** — ensure not cleared on failed recovery

**Risk**: The atomicity gap in runtime checkpoint writes cannot be fixed without modifying frozen runtime. S9-06 will document this gap and ensure Project-level atomicity.

**Verdict**: Proceed to Phase B (Contract Decision) and Phase C (Implementation) with minimal, additive changes per audit findings.

---

## 17. Artifacts

- `artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_AUDIT.md` (this document)

**Next Step**: Phase B — Contract Decision based on audit findings.
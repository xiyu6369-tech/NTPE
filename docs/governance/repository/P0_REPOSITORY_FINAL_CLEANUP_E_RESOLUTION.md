# P0 Repository Final Cleanup — STOP-02 Core WIP Resolution

## Executive Summary

All 3 E-classified (Ambiguous) files have been investigated and resolved:

| File | Resolution | E → |
|------|------------|-----|
| `core/adapters/production_submission_adapter.py.new` | **REMOVE** — Exact duplicate of tracked file | D |
| `core/context_scene_memory/persistence.py` | **KEEP** — Legitimate production module, missing from git tracking | A |
| `core/translation_runtime/boundary_detector.py` | **KEEP** — Legitimate production module, missing from git tracking | A |

**Result: E = 0 | STOP-02 = CLEAR**

---

## E-01: `core/adapters/production_submission_adapter.py.new`

### Investigation Results

| Item | Result |
|------|--------|
| **Path** | `core/adapters/production_submission_adapter.py.new` |
| **Git State** | Untracked (??) — Not in HEAD (61fc7d3), not in origin/main |
| **File Size** | 10,551 bytes (256 lines) |
| **Last Modified** | 2026-08-14 21:27 |

### Content Analysis

**Exact duplicate** of `core/adapters/production_submission_adapter.py` (tracked in HEAD):

```bash
# Verified: byte-for-byte identical
diff core/adapters/production_submission_adapter.py core/adapters/production_submission_adapter.py.new
# No output = identical
```

**API Surface** (both files):
- `TranslationJobRequest` — Dataclass with 29 fields for translation job configuration
- `SubmissionResult` — Dataclass for submission outcome
- `SourceIdentity` — Dataclass for source file identity
- `ProductionSubmissionAdapter` — Class with methods:
  - `compute_source_identity()` — Deterministic SHA-256 source hash
  - `_compute_config_fingerprint()` — Config fingerprint for job identity
  - `_compute_submission_identity()` — Combined job ID
  - `build_cli_argv()` — CLI argument construction
  - `submit()` — Async subprocess submission
  - `submit_sync()` — Synchronous submission with timeout

### Dependencies

**Imports**: `hashlib`, `json`, `os`, `subprocess`, `sys`, `time`, `dataclasses`, `pathlib`, `typing`

**Consumers (Production)**:
- `tests/unit/adapters/test_production_submission_adapter.py` — 31 tests, ALL PASS
- No other production code imports this module

### Production Reachability

```
Caller: tests/unit/adapters/test_production_submission_adapter.py
  ↓
Module: core.adapters.production_submission_adapter (tracked version)
  ↓
Production Runtime: NO — Only used in tests
  ↓
Stage 5 Execution Path: NO
```

The tracked version (`production_submission_adapter.py`) is in HEAD and has test coverage. The `.new` duplicate has **zero production consumers**.

### Stage 5 Authorization

**NO** — Not mentioned in any Stage 5 Batch 5.x specification or governance document as a new file. The tracked version was introduced in P0 Stage 1/2 (per `P0_STAGE1_INTEGRATED_ACCEPTANCE_REPORT.md` and `P0_STAGE2_IMPLEMENTATION_REPORT.md`).

### Frozen Contract Relation

**NONE** — This is an adapter/wrapper for CLI submission, not part of any frozen contract.

### Governance History

| Document | Classification |
|----------|----------------|
| `P0_STAGE5_BATCH5_1_GIT_DELIVERY_RECONCILIATION.md` | **E** — "Temporary/.new file" — MUST NOT commit |
| `P0_STAGE5_BATCH5_2_GIT_DELIVERY_RECONCILIATION.md` | **D** — "Generated/artifact/temp: temporary .new file" |
| `P0_STAGE5_BATCH5_3_GIT_DELIVERY_RECONCILIATION.md` | **D** — "Temporary — do not commit" |
| `P0_STAGE5_BATCH5_4_GIT_DELIVERY_RECONCILIATION.md` | **D** — "Generated/Artifact: Temporary file" |
| `P0_STAGE5_BATCH5_5_GIT_DELIVERY_RECONCILIATION.md` | **D** — "Generated/Artifact: Temporary file" |
| `P0_STAGE5_BATCH5_6_GIT_DELIVERY_RECONCILIATION.md` | **C** — "Pre-existing: Untracked modification" |
| `P0_STAGE5_BATCH5_7_GIT_DELIVERY_RECONCILIATION.md` | **C** — "Pre-existing temporary file" |
| `P0_STAGE5_BATCH5_8_1_GIT_DELIVERY_RECONCILIATION.md` | "Pre-existing build artifact" |
| `P0_STAGE5_FINAL_ACCEPTANCE_REVIEW.md` | **E** — "Ambiguous — likely work-in-progress" |
| `P0_STAGE1_INTEGRATED_ACCEPTANCE_REPORT.md` | Cleanup item: "Delete `production_submission_adapter.py.new` (stray file)" |

**Consensus across 10+ governance docs: This is a stray/temporary/duplicate file.**

### Final Classification: **REMOVE**

**Rationale**: 
1. Byte-for-byte duplicate of tracked file in HEAD
2. Zero production consumers (only tests use the tracked version)
3. `.new` suffix indicates temporary/stray status
4. 10+ governance documents consistently classify as temporary/artifact
5. No Stage 5 authorization
6. No frozen contract relation

**Action**: Delete file. No git tracking needed (already untracked).

---

## E-02: `core/context_scene_memory/persistence.py`

### Investigation Results

| Item | Result |
|------|--------|
| **Path** | `core/context_scene_memory/persistence.py` |
| **Git State** | Untracked (??) — **NOT in HEAD (61fc7d3)**, not in origin/main |
| **File Size** | 4,289 bytes (134 lines) |
| **Last Modified** | 2026-08-18 14:17 |

### Content Analysis

**Complete persistence layer implementation** for Context/Scene Memory:

**Public API** (exported in `core/context_scene_memory/__init__.py`):
```python
compute_book_identity(input_path: Path, project_name: str) -> str
get_context_memory_file_path(output_dir: Path, book_identity: str) -> Path
save_context_memory(store: ContextMemoryStore, memory_file: Path) -> dict
load_context_memory(memory_file: Path) -> ContextMemoryStore
verify_context_memory_integrity(memory_file: Path, expected_hash: str) -> bool
load_or_create_context_memory(*, output_dir, input_path, project_name) -> tuple[ContextMemoryStore, dict]
```

**Key Features**:
- Deterministic book identity (SHA-256 of `project_name|input_path`)
- Artifact-isolated file paths (`context_scene_memory_{book_identity}.json`)
- Fail-closed deserialization with schema validation
- Hash verification for checkpoint/resume integrity
- Priority: existing v2 file → fresh store

### Dependencies

**Imports**: `hashlib`, `pathlib`, `typing`, `.models`, `.serialization`, `.store`, `.validation`

### Production Consumers (Verified)

| Consumer | Location | Usage |
|----------|----------|-------|
| LTS Translation Runtime | `lts/txt_translation_runtime.py:72,78,680,1018,1022,1054,1058` | `compute_book_identity`, `load_or_create_context_memory`, `save_context_memory` |
| Series Orchestration Runtime Integration | `core/series_orchestration/runtime_integration.py:153,155` | `load_or_create_context_memory` |
| Series Checkpoint Validation | `core/series_checkpoint/validation.py:73` | `get_context_memory_file_path` |
| Series Checkpoint Recovery | `core/series_checkpoint/recovery.py:268` | `get_context_memory_file_path` |
| Series Checkpoint Manager | `core/series_checkpoint/manager.py:92` | `get_context_memory_file_path` |
| Character Memory v2 Persistence | `core/character_memory_v2/persistence.py:236` | `compute_book_identity` (DUPLICATE - see below) |
| Series Orchestration Coordinator | `core/series_orchestration/coordinator.py:118,119` | `compute_book_identity` (DUPLICATE - see below) |

### Production Reachability

```
Caller: lts/txt_translation_runtime.py (LTS Pipeline)
  ↓
Module: core.context_scene_memory.persistence
  ↓
Production Runtime: YES — Loaded per-book when enable_cross_chunk_context=True
  ↓
Stage 5 Execution Path: YES — Integrated into RuntimeOrchestrator.execute() via metadata
```

**VERIFIED**: The module is actively used in the production LTS pipeline when the feature flag is enabled.

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/unit/test_context_scene_memory_persistence.py` | 16 | **ALL PASS** |
| `tests/unit/test_context_scene_memory.py` | 18 | **ALL PASS** (includes persistence API exports) |

**Key Test Coverage**:
- Deterministic book identity
- Save/load roundtrip
- Hash verification
- Fail-closed on missing/corrupted/empty/schema-mismatch files
- Fresh store creation
- Existing file loading
- Per-book isolation
- Scene state persistence
- Context selection after reload
- Deterministic serialization

### Stage 5 Authorization

**YES (Implicit)** — This module was implemented in **Stage 4 Batch 3D-2** (Context/Scene Memory Production Persistence) and accepted:

> **P0_STAGE4_BATCH3D2_CONTEXT_MEMORY_PERSISTENCE_ACCEPTANCE_REPORT.md** — Status: ACCEPTED
> - `core/context_scene_memory/persistence.py` — **NEW** — Persistence layer (134 lines)
> - All 16 persistence tests PASS
> - All validation gates PASS (ntpe_validate, compileall, git diff --check)

However, **the file was never committed to git** — it exists only in the working directory.

### Frozen Contract Relation

**NONE** — Additive persistence layer. Frozen contracts unchanged per acceptance report:
- Checkpoint Identity: ✅ Unmodified (metadata additive)
- Deterministic Identity: ✅ Uses deterministic source identity
- Artifact Isolation: ✅ Memory files in output directory
- Fail-closed Behavior: ✅ All deserialization fail-closed

### Duplicate Function Alert

**`compute_book_identity` exists in TWO locations:**
1. `core/context_scene_memory/persistence.py:19` (this file)
2. `core/character_memory_v2/persistence.py:40` (tracked in HEAD)

Both implementations are **identical**. This is a known duplication from Stage 4 Batch 3D-2 design (shared identity function). The character_memory_v2 version is the "canonical" one used by Series orchestration; the context_scene_memory version is for Context/Scene Memory isolation.

### Final Classification: **KEEP** (and add to git tracking)

**Rationale**:
1. **Legitimate production module** — Implemented in Stage 4 Batch 3D-2, accepted, tested
2. **Production reachability VERIFIED** — Used in LTS pipeline, Series orchestration, Series checkpoint
3. **16 dedicated tests + 18 integration tests ALL PASS**
4. **Zero Provider/Network/Translation executions** in tests
5. **Frozen contracts preserved** (additive only)
6. **Was supposed to be committed** in Batch 3D-2 but wasn't
7. **Required for Stage 5** — Series checkpoint/resume uses `get_context_memory_file_path`

**Action**: Add to git tracking (`git add core/context_scene_memory/persistence.py`)

---

## E-03: `core/translation_runtime/boundary_detector.py`

### Investigation Results

| Item | Result |
|------|--------|
| **Path** | `core/translation_runtime/boundary_detector.py` |
| **Git State** | Untracked (??) — **NOT in HEAD (61fc7d3)**, not in origin/main |
| **File Size** | 5,411 bytes (155 lines) |
| **Last Modified** | 2026-08-10 12:50 |

### Content Analysis

**Scene/Chapter Boundary Detection** for Context/Scene Memory:

**Public API**:
```python
class BoundaryResult:
    type: BoundaryType
    scene_id: Optional[str]
    chapter_id: Optional[str]
    confidence: float
    metadata: Optional[Dict[str, Any]]

def detect_boundary(prev_chunk: str, curr_chunk: str) -> BoundaryResult
```

**BoundaryType** (from `core.context_scene_memory.models`):
- `SAME_SCENE` (default, confidence=1.0)
- `SCENE_TRANSITION` (explicit scene marker, confidence=0.9)
- `CHAPTER_TRANSITION` (explicit chapter marker, confidence=0.95)
- `UNKNOWN_TRANSITION` (heuristics: location/time/speaker change)

**Detection Logic** (Conservative):
1. Chapter markers (Korean/Chinese/English "Chapter N") → CHAPTER_TRANSITION
2. Scene markers (Korean/Chinese/English "Scene N", `***` separators) → SCENE_TRANSITION
3. Location shift heuristics → UNKNOWN_TRANSITION (confidence 0.4)
4. Time shift + paragraph break → UNKNOWN_TRANSITION (confidence 0.3)
5. Speaker change at paragraph boundary → UNKNOWN_TRANSITION (confidence 0.2)
6. Default → SAME_SCENE

### Dependencies

**Imports**: `re`, `dataclasses`, `typing`, `core.context_scene_memory.models.BoundaryType`

### Production Consumers (Verified)

| Consumer | Location | Usage |
|----------|----------|-------|
| LTS Translation Runtime | `lts/txt_translation_runtime.py:647,795,849` | `detect_boundary`, `BoundaryResult` — called per-chunk for scene tracking |

### Production Reachability

```
Caller: lts/txt_translation_runtime.py (LTS Pipeline)
  ↓
Module: core.translation_runtime.boundary_detector
  ↓
Production Runtime: YES — Called per-chunk during translation
  ↓
Stage 5 Execution Path: YES — Scene state fed into Context/Scene Memory store
```

**VERIFIED**: The module is actively called in the LTS pipeline during translation to detect scene/chapter boundaries and update Context/Scene Memory scene state.

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/unit/translation_runtime/test_boundary_detector.py` | 13 | **ALL PASS** |
| `tests/unit/rm8_phase6_reader_outcome_test.py` | 5+ | **ALL PASS** (uses boundary_detector) |

**Test Coverage**:
- Chapter transition detection (Korean, Chinese, English)
- Scene transition detection (Korean, Chinese, English, `***`)
- Location shift heuristic
- Time shift heuristic
- Speaker change heuristic
- Conservative default (SAME_SCENE)
- BoundaryResult serialization

### Stage 5 Authorization

**YES (Implicit)** — Specified in **Stage 4 Batch 3B** architecture reconciliation:

> `P0_STAGE4_BATCH3B_MEMORY_ARCHITECTURE_RECONCILIATION.md:386`:
> | Boundary detection | ✅ | `boundary_detector.py` specified but not implemented |

And implemented in **Stage 4 Batch 3D** (per Batch 3D preflight):

> `P0_STAGE4_BATCH3D_MEMORY_PERSISTENCE_PREFLIGHT.md:213`:
> **File:** `core/translation_runtime/boundary_detector.py`

The implementation exists and is used, but **was never committed to git**.

### Frozen Contract Relation

**NONE** — Pure detection utility. No frozen contracts modified. Used by Context/Scene Memory which is additive.

### Final Classification: **KEEP** (and add to git tracking)

**Rationale**:
1. **Legitimate production module** — Specified in Stage 4 Batch 3B, implemented by Stage 4 Batch 3D
2. **Production reachability VERIFIED** — Called per-chunk in LTS pipeline for scene tracking
3. **13 dedicated tests + integration tests ALL PASS**
4. **Zero Provider/Network/Translation executions** in tests
5. **Frozen contracts preserved** (pure utility, no contract changes)
6. **Required for Context/Scene Memory** — Scene state updates depend on boundary detection
7. **Was supposed to be committed** but wasn't

**Action**: Add to git tracking (`git add core/translation_runtime/boundary_detector.py`)

---

## Summary Matrix

| File | Git State | Production Reachability | Tests | Stage 4 Auth | Stage 5 Auth | Frozen Contract | Classification |
|------|-----------|------------------------|-------|--------------|--------------|-----------------|----------------|
| `production_submission_adapter.py.new` | Untracked duplicate | NO (tests only) | 31 tests (on tracked) | NO | NO | NONE | **REMOVE** |
| `context_scene_memory/persistence.py` | Untracked (missing commit) | **YES** (LTS, Series, Checkpoint) | 16 + 18 = 34 | **YES** (Batch 3D-2) | Implicit | NONE (additive) | **KEEP** |
| `translation_runtime/boundary_detector.py` | Untracked (missing commit) | **YES** (LTS per-chunk) | 13 + 5+ = 18+ | **YES** (Batch 3B/3D) | Implicit | NONE | **KEEP** |

---

## STOP-02 Resolution Confirmation

```
E-01: RESOLVED → REMOVE (D)
E-02: RESOLVED → KEEP (A)
E-03: RESOLVED → KEEP (A)

E-classified files: 0
STOP-02: CLEAR
```

---

## Next Steps (Post-Resolution)

With STOP-02 cleared, the cleanup can proceed to implementation phase. The two KEEP files require:

1. `git add core/context_scene_memory/persistence.py`
2. `git add core/translation_runtime/boundary_detector.py`
3. Commit as part of appropriate atomic batch (likely Batch A or new Batch)

The REMOVE file (`production_submission_adapter.py.new`) can be deleted immediately as it's untracked.

---

## Verification Commands

```powershell
# Verify E=0
git status --porcelain | Where-Object { $_ -match '^\?\?' } | ForEach-Object {
    if ($_ -match 'production_submission_adapter\.py\.new|context_scene_memory/persistence\.py|translation_runtime/boundary_detector\.py') {
        $_
    }
}

# Should return only production_submission_adapter.py.new (to be removed)
# The other two should be staged after git add

# Verify production reachability still works
python -m pytest tests/unit/test_context_scene_memory_persistence.py -v
python -m pytest tests/unit/translation_runtime/test_boundary_detector.py -v
python -m pytest tests/unit/adapters/test_production_submission_adapter.py -v

# Full validation
python ntpe_validate.py
python -m compileall core/
git diff --check
```

---

**Document Created:** 2026-08-23  
**Baseline:** 61fc7d359a9e3e1e51c66b0909aec86a3baf3831  
**Investigation:** Evidence-based, no modifications performed
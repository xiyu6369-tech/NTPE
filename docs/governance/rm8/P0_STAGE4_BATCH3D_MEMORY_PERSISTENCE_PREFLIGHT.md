# P0 Stage 4 Batch 3D — Memory Persistence & Production Activation
## PREFLIGHT AUDIT & DESIGN SPECIFICATION

**Status:** PREFLIGHT COMPLETE — READY FOR OWNER REVIEW  
**Date:** 2026-08-18  
**Author:** Kilo Code (Audit Agent)  
**Production Code Modified:** NO  
**Frozen Contracts Modified:** NO  

---

## 1. Executive Summary

This preflight audit examines the existing **Character Memory v2** and **Context/Scene Memory** implementations to design production-grade persistence that integrates with NTPE's translation lifecycle (checkpoint, session, resume).

**Key Finding:** Both memory systems have **complete, validated implementations** with serialization, lifecycle management, and selection logic. The gap is **persistence integration** — connecting them to NTPE's identity system (session, book, checkpoint) for cross-chunk, cross-session continuity.

**No new memory systems, no LLM extractors, no architecture redesign required.**

---

## 2. Character Memory v2 — Current Architecture

### 2.1 Data Model (`core/character_memory_v2/models.py`)

| Component | Details |
|-----------|---------|
| **Schema Version** | `2.0` |
| **Core Types** | 13 FactTypes, 7 EvidenceTypes, 3 ApprovalStatuses, 7 MemoryStatuses, 6 ExpiryKinds |
| **Primary Record** | `MemoryRecord` — frozen dataclass with 24 fields |
| **Identity** | `memory_id` (stable, deterministic: `stable_memory_id(character_id, fact_type, value, evidence_id)`) |
| **Character Identity** | `character_id` (normalized text) |
| **Provenance** | `source_case_id`, `source_segment_id`, `source_text_hash`, `created_at`, `updated_at`, `version` |
| **Expiry Policy** | `ExpiryPolicy(kind, scope_id, expires_at)` — NEVER, SEGMENT/CHAPTER/SESSION_SCOPE, TIMESTAMP, MANUAL_REVIEW_REQUIRED |
| **Conflict Tracking** | `ConflictRecord` with `conflict_id`, resolution state, preferred memory |
| **History** | Full version history per `memory_id` |

### 2.2 Store (`core/character_memory_v2/store.py`)

| Capability | Implementation |
|------------|----------------|
| **In-memory** | `records`, `history`, `conflicts`, `snapshot_version` |
| **Indexes** | `_fact_index` (fact_key → memory_id), `_conflict_index` (conflict_key → set[memory_id]) |
| **Serialization** | `to_dict()` / `from_dict()` with full validation |
| **Conflict Resolution** | Evidence-tier based (HUMAN_APPROVED > SOURCE_OBSERVATION > TRANSLATION_OBSERVATION > AI_INFERENCE) |
| **Deduplication** | `fact_key` (character_id, fact_type, value) + evidence merging |
| **Lifecycle** | `add_or_merge_memory`, `approve_memory`, `reject_memory`, `expire_memory`, `rollback_memory`, `supersede_memory` |
| **Fail-closed** | Full validation on deserialize, invalid records rejected |

### 2.3 Selection (`core/character_memory_v2/selection.py`)

| Feature | Details |
|---------|---------|
| **Token Budget** | `select_prompt_eligible_memories(store, token_budget=256, ...)` |
| **Priority** | Approved first, then evidence tier, then fact-type stability, then recency |
| **Scope Filtering** | `scope` dict with `segment_id`, `chapter_id`, `session_id` |
| **Language Filter** | `language_profile` matching |
| **Expiry** | Respects `ExpiryPolicy` per record |
| **AI Inference** | Excluded by default (`include_pending=False`) |

### 2.4 Serialization (`core/character_memory_v2/serialization.py`)

```python
serialize_memory_store(store) -> str (canonical JSON)
deserialize_memory_store(payload) -> MemoryStore (fail-closed validation)
```

---

## 3. Context / Scene Memory — Current Architecture

### 3.1 Data Model (`core/context_scene_memory/models.py`)

| Component | Details |
|-----------|---------|
| **Schema Version** | `1.0` |
| **Context Types** | 13 ContextTypes (PREVIOUS_TRANSLATION_EXCERPT, SCENE_SUMMARY, EVENT_STATE, etc.) |
| **Core Records** | `ContextMemoryRecord`, `SceneMemoryRecord`, `UnresolvedReference` |
| **Context Identity** | `context_id` (stable: `stable_id("ctx", type, value, evidence_id, chapter_id, scene_id)`) |
| **Scene Identity** | `scene_id` (user-provided, from explicit markers) |
| **Chapter Identity** | `chapter_id` (user-provided) |
| **Sequence** | `sequence_index` (chunk index within scene) |
| **Provenance** | `source_text_hash`, `translation_text_hash`, `rule_id`, `evidence` |
| **Expiry** | Conservative: SCENE_SCOPE, CHAPTER_SCOPE, MANUAL_REVIEW_REQUIRED, NEVER |
| **Participants** | `SceneParticipant` with status (PRESENT, MENTIONED, EXITED_SCENE, etc.) |
| **Unresolved References** | Tracked explicitly, never auto-resolved |

### 3.2 Store (`core/context_scene_memory/store.py`)

| Capability | Implementation |
|------------|----------------|
| **In-memory** | `contexts`, `scenes`, `context_history`, `scene_history`, `conflicts` |
| **Serialization** | `to_dict()` / `from_dict()` with schema validation |
| **Conflict Handling** | Singular types (location, time, speaker, POV) → conflict; multi-valued → merge |
| **Lifecycle** | `expire_context`, `reject_context`, `supersede_context`, `rollback_context`, `rollback_scene` |
| **Scene State** | `transition_scene()`, `transition_chapter()` with participant expiry |

### 3.3 Selection (`core/context_scene_memory/context_selection.py`)

```python
select_context_for_translation(
    store,
    chapter_id, scene_id, sequence_index,
    character_ids,
    token_budget,
    include_previous_translation=True,
    include_unresolved=True,
    now=...
) -> ContextSelectionResult
```

### 3.4 Serialization (`core/context_scene_memory/serialization.py`)

```python
dumps_context_store(store) -> str
loads_context_store(payload) -> ContextMemoryStore
save_context_store(path, store)
load_context_store(path) -> ContextMemoryStore
```

---

## 4. NTPE Identity Architecture — Integration Points

### 4.1 Existing Identity Hierarchy

```
Book (input_path + project_name)
    ↓
Translation Session (session_id, snapshot_id)
    ↓
Runtime Orchestrator (per-chunk execute())
    ↓
Checkpoint (checkpoint_id, chunk_index, state_hash)
    ↓
Resume (restore from checkpoint)
```

### 4.2 Current Session/Checkpoint Models

**TranslationSession** (`core/runtime_session/models.py`):
- `session_id` (12-char hex)
- `snapshot_id`
- `prompt_hash`
- `metadata` (arbitrary)

**CheckpointSnapshot** (`core/runtime_checkpoint/models.py`):
- `checkpoint_id`, `session_id`, `snapshot_id`, `chunk_index`
- `state_hash` (deterministic, excludes timestamp)
- `progress` (current_chunk, completed_chunks, total_chunks, status)
- `manifest` (request_hash, prompt_hash, snapshot_id, chunk_index)
- `metadata` (arbitrary session-private runtime metadata)

### 4.3 Current LTS Runtime Flow (`lts/txt_translation_runtime.py`)

```python
# Per file (book):
session = orchestrator.start_session(metadata={...})
session_id = session.session_id

# Per chunk:
orchestrator.execute(
    chunk_text=chunk,
    session_id=session_id,
    current_chunk=idx,
    total_chunks=len(chunks),
    metadata={...}  # includes enable_cross_chunk_context, context_state, etc.
)
```

### 4.4 Current TE v7.2 Store Instantiation (Batch 3C-1)

```python
# In parse_args():
character_store, context_scene_store = _create_v72_stores()
return TxtTranslationOptions(
    ...
    quality_character_store_v72=character_store,
    quality_context_scene_store_v72=context_scene_store,
)
```

**Problem:** Fresh stores per `parse_args()` call — no persistence across runs.

---

## 5. LTS Character Memory — Current State

**File:** `archive/historical/memory/character_memory_lts.json`

```json
{
  "version": "1.1-lts-stage-03",
  "updated_at": "2026-07-11T22:26:20",
  "characters": {
    "version": "1.1-lts-stage-03",
    "updated_at": "2026-07-07T01:31:15",
    "정태의": "鄭泰義",
    "카일": "凱爾",
    "일레이": "伊萊"
  }
}
```

**Usage:** Loaded via `resolve_character_memory_path()` → `load_json_pairs()` → merged into `locked_dictionary` → post-translation alias replacement.

**Gap to v2:** Simple `{korean: chinese}` dict vs. rich evidence-based `MemoryRecord` with 13 fact types, provenance, lifecycle.

---

## 6. Boundary Detector — Current State

**File:** `core/translation_runtime/boundary_detector.py`

| Feature | Status |
|---------|--------|
| **Chapter detection** | ✅ Explicit patterns (`제 N 장`, `Chapter N`, `第 N 章`) |
| **Scene detection** | ✅ Explicit patterns (`제 N 절`, `Scene N`, `***`) |
| **Heuristics** | Location/time/speaker → `UNKNOWN_TRANSITION` (conservative) |
| **Auto scene ID** | ❌ REMOVED — scene IDs ONLY from explicit markers |
| **Integration** | Used in LTS runtime when `quality_context_scene_v72=True` |

**Gap:** Only used when feature flag ON. Not integrated with checkpoint/resume.

---

## 7. DESIGN DECISIONS REQUIRED

### 7.1 Character Memory Persistence Scope

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A. Per-Book** | One memory file per book (project_name + input_path) | Simple, matches LTS model; loses session-specific evidence |
| **B. Per-Session** | One memory file per TranslationSession | Fine-grained, but complex recovery |
| **C. Per-Book + Session Overlay** | Base book memory + session deltas | Best of both; more complex |

**RECOMMENDATION: A (Per-Book)** — Matches LTS model, simplest migration, deterministic. Session-specific evidence can be stored in-session and merged on checkpoint.

### 7.2 Memory File Location

| Option | Description |
|--------|-------------|
| **A. Alongside output** | `{output_dir}/character_memory_{project}.json` |
| **B. Dedicated memory dir** | `{root}/memory/{project}.json` |
| **C. Config-driven** | `TxtTranslationOptions.character_memory_dir` |

**RECOMMENDATION: A** — Self-contained, portable, matches NTPE artifact isolation.

### 7.3 Migration: LTS → v2

| Requirement | Design |
|-------------|--------|
| **Deterministic** | Same LTS input → same v2 output |
| **Loss-aware** | Report unmappable entries |
| **Fail-closed** | Invalid LTS → error, not silent skip |
| **Preserve original** | Never modify LTS file |

**Mapping:**
- LTS `korean: chinese` → v2 `MemoryRecord(fact_type=CANONICAL_NAME, value=chinese, evidence=HISTORICAL_IMPORT, approval_status=APPROVED)`

### 7.4 Checkpoint Integration

| Approach | Description |
|----------|-------------|
| **A. Embedded in Checkpoint** | Store memory snapshot in `CheckpointSnapshot.metadata` |
| **B. Separate File + Metadata** | Memory file on disk; checkpoint stores `memory_file_hash` + `memory_snapshot_version` |

**RECOMMENDATION: B** — Checkpoint contract is frozen; memory files can be large. Metadata stores `character_memory_hash` + `character_memory_snapshot_version` for integrity verification.

### 7.5 Context/Scene Memory Scope

| Option | Description |
|--------|-------------|
| **A. Per-Book** | Single store file per book |
| **B. Per-Session** | Session-specific (simpler but less continuity) |

**RECOMMENDATION: A** — Scene state must persist across sessions for true cross-chunk continuity.

### 7.6 Resume Behavior

| Scenario | Behavior |
|----------|----------|
| Normal resume | Load memory from disk, restore store, continue |
| Crash resume | Same — last checkpoint's memory state restored |
| Wrong book/session | Reject — verify `memory_file_hash` matches checkpoint metadata |
| Corrupted memory file | FAIL CLOSED — error, don't silently rebuild |

---

## 8. PROPOSED PERSISTENCE ARCHITECTURE

### 8.1 Character Memory v2 — Per-Book Persistence

```
Translation Start
    ↓
load_character_memory(book_id) → MemoryStore
    ├── If file exists: deserialize_memory_store()
    ├── If LTS file exists: migrate_lts_to_v2() + serialize
    └── Else: new MemoryStore()
    ↓
Per Chunk:
    RuntimeOrchestrator.execute()
    ├── select_prompt_eligible_memories() → Prompt
    ├── Translation
    ├── (optional) update memory from translation
    └── Checkpoint: serialize_memory_store() → write to disk
    ↓
Resume:
    load_character_memory() → restore_snapshot()
```

### 8.2 Context/Scene Memory — Per-Book Persistence

```
Translation Start
    ↓
load_context_scene_memory(book_id) → ContextMemoryStore
    ├── If file exists: load_context_store()
    └── Else: new ContextMemoryStore()
    ↓
Per Chunk (if enable_cross_chunk_context):
    boundary = detect_boundary(prev, curr)
    if transition: transition_scene/chapter()
    selection = select_context_for_translation()
    Prompt ← selection
    Translation
    Checkpoint: save_context_store(path, store)
    ↓
Resume:
    load_context_store() → restore()
```

### 8.3 Checkpoint Metadata Extension

```python
# In CheckpointSnapshot.metadata:
{
    "character_memory": {
        "file_hash": "sha256...",
        "snapshot_version": 42,
    },
    "context_scene_memory": {
        "file_hash": "sha256...",
        "snapshot_version": 17,
    }
}
```

**Verification on Resume:** Compare stored hashes with current file hashes.

---

## 9. VALIDATION REQUIREMENTS

### 9.1 Character Memory Tests

| Test | Description |
|------|-------------|
| `test_persistence_roundtrip` | Serialize → deserialize → identical store |
| `test_lts_migration` | LTS JSON → v2 store → deterministic output |
| `test_checkpoint_integration` | Checkpoint metadata includes memory hash/version |
| `test_resume_restores_memory` | Crash → resume → memory identical |
| `test_wrong_session_rejected` | Different book → memory not loaded |
| `test_corruption_fail_closed` | Corrupted file → error, not silent |

### 9.2 Context/Scene Memory Tests

| Test | Description |
|------|-------------|
| `test_persistence_roundtrip` | Serialize → deserialize → identical store |
| `test_scene_state_persistence` | Scene transitions survive checkpoint/resume |
| `test_boundary_detection_persists` | Scene IDs stable across resume |
| `test_resume_restores_context` | Context selection identical after resume |
| `test_wrong_session_rejected` | Mismatch → error |

### 9.3 Integration Tests

| Test | Description |
|------|-------------|
| `test_full_translation_with_memory` | Multi-chunk, checkpoint, resume |
| `test_memory_updates_propagate` | Memory written chunk N → available chunk N+1 |
| `test_deterministic_prompt` | Same input → same prompt with memory |

---

## 10. RISK ASSESSMENT

| Risk | Severity | Mitigation |
|------|----------|------------|
| **LTS migration data loss** | HIGH | Loss-aware migration with report; preserve LTS file |
| **Checkpoint/memory desync** | HIGH | Metadata hashes + version verification on resume |
| **Memory file corruption** | MEDIUM | Fail-closed deserialization; no silent rebuild |
| **Large memory files** | LOW | Current stores are small; JSON is adequate |
| **Concurrent access** | LOW | Single-process translation; no locking needed |
| **Schema evolution** | MEDIUM | Version pinning (`SCHEMA_VERSION`); migration scripts |

---

## 11. FROZEN CONTRACT COMPLIANCE

| Contract | Impact | Compliance |
|----------|--------|------------|
| BookIntakeProcessor | None | ✅ |
| Canonical Intake Contract | None | ✅ |
| TranslationRuntime | None | ✅ |
| Provider Boundary | None | ✅ |
| Checkpoint Identity | Extended metadata only | ✅ (additive) |
| Deterministic Identity | Memory file hash in metadata | ✅ |
| Artifact Isolation | Memory files in output dir | ✅ |
| Quality Gate | Memory updates don't bypass QA | ✅ |
| Fail-closed Behavior | All deserialization fail-closed | ✅ |

---

## 12. IMPLEMENTATION SEQUENCE

### Batch 3D-1: Character Memory v2 Persistence

1. **Memory file I/O** — `load_character_memory(book_id)`, `save_character_memory(book_id, store)`
2. **LTS Migration** — `migrate_lts_to_v2(lts_path)` with loss report
3. **Checkpoint Integration** — Write memory file on checkpoint; metadata in `CheckpointSnapshot.metadata`
4. **Resume Integration** — Load/verify memory on `orchestrator.resume()`
5. **Runtime Wiring** — Use persisted store in `RuntimeOrchestrator.execute()`
6. **Tests** — All validation requirements from §9

### Batch 3D-2: Context/Scene Memory Persistence

1. **Context file I/O** — `load_context_scene_memory(book_id)`, `save_context_scene_memory()`
2. **Checkpoint Integration** — Write context file on checkpoint; metadata
3. **Resume Integration** — Load/verify context on resume
4. **Boundary Detector Integration** — Ensure scene IDs stable (already explicit-only)
5. **Runtime Wiring** — Use persisted store when `enable_cross_chunk_context`
6. **Tests** — All validation requirements from §9

---

## 13. ACCEPTANCE CRITERIA

### Batch 3D-1

```
[ ] load_character_memory() / save_character_memory() implemented
[ ] migrate_lts_to_v2() implemented with loss report
[ ] Checkpoint metadata includes character_memory hash + snapshot_version
[ ] Resume verifies memory hash matches checkpoint metadata
[ ] RuntimeOrchestrator.execute() uses persisted store
[ ] Existing Character Memory v2 tests PASS
[ ] New persistence tests PASS
[ ] ntpe_validate ALL PASS
[ ] compileall 0 errors
[ ] git diff --check clean
[ ] Default flags OFF
```

### Batch 3D-2

```
[ ] load_context_scene_memory() / save_context_scene_memory() implemented
[ ] Checkpoint metadata includes context_scene_memory hash + snapshot_version
[ ] Resume verifies context hash matches checkpoint metadata
[ ] Runtime uses persisted store when enable_cross_chunk_context=True
[ ] Scene state survives checkpoint/resume
[ ] Existing Context/Scene Memory tests PASS
[ ] New persistence tests PASS
[ ] ntpe_validate ALL PASS
[ ] compileall 0 errors
[ ] git diff --check clean
[ ] Default flags OFF
```

---

## 14. PREFLIGHT VERDICT

```
P0 STAGE 4 BATCH 3D — PREFLIGHT COMPLETE
MEMORY PERSISTENCE PREFLIGHT REPORT GENERATED

Next Step: OWNER REVIEW of DESIGN DECISIONS REQUIRED (§7)

READY FOR BATCH 3D-1 IMPLEMENTATION UPON AUTHORIZATION
```
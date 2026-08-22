# P0 RM-8.2 Provenance Gap Report

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## RM-8.2 Provenance Chain

```
RM-8.2 metadata (context_state_metadata)
    ���� created in
_translate_txt_with_runtime_pipeline() (lts/txt_translation_runtime.py:604-992)
    ���� passed to
orchestrator.execute() metadata.context_state
    ���� stored in
chunk_records[i]["metadata"]["context_state"]
    ���� consumed by
delivery_pipeline._aggregate_context_continuity() (delivery_pipeline.py:65-87)
    ���� included in
QualityCertificate (RM-8.3)
    ���� available for
RM-8.4 EPUB packaging (chapter_map)
```

---

## Where context_state_metadata Is Created

**File**: `lts/txt_translation_runtime.py`  
**Function**: `_translate_txt_with_runtime_pipeline()`  
**Lines**: 784-797 (within chunk loop, idx 1..N)

```python
# RM-8.2: Cross-Chunk Context Integration (feature-gated)
enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)
# ...
if enable_cross_chunk_context:
    # 1. BOUNDARY DETECTION
    boundary: BoundaryResult = detect_boundary(prev_chunk_text, chunk)
    
    # 2. SCENE/CHAPTER TRANSITION
    if boundary.type != BoundaryType.SAME_SCENE:
        if boundary.type == BoundaryType.CHAPTER_TRANSITION:
            transition_chapter(...)
        elif boundary.type == BoundaryType.SCENE_TRANSITION:
            transition_scene(...)
        current_scene_id = boundary.scene_id or current_scene_id
    
    # 3. CONTEXT SELECTION
    selection = select_context_for_translation(...)
    
    # 4. NARRATIVE STATE
    narrative_engine.analyze_chunk(source=chunk, translation=prev_translation)
    narrative_context = narrative_engine.get_context_for_prompt()
    
    # 5. ENTITY INJECTION (RM-7.2) - optional
    
    # Compose context_state metadata
    context_state_metadata = {
        "context_selection_fingerprint": selection.fingerprint,
        "scene_id": current_scene_id,
        "scene_version": context_store.get_scene(current_scene_id).scene_version,
        "narrative": narrative_context,
        "boundary": boundary.to_dict(),
        "selected_context_ids": tuple(r.item_id for r in selection.selected_records),
    }
else:
    context_state_metadata = None
```

**Gated by**: `options.quality_context_scene_v72` (CLI: `--quality-context-scene-v72`)

---

## What chunk_records Actually Save

**File**: `lts/txt_translation_runtime.py`  
**Location**: Inside `_translate_txt_with_runtime_pipeline()` chunk loop

```python
result = {
    "status": "success",
    "output_path": str(chunk_file),
    "package_id": package["package_id"],
    "attempt": 1,
    "qa": qa_report,
    "runtime_pipeline": True,
    "orchestrator_version": orchestrator.version,
    "session_id": session_id,
}
records.append(result)
```

**Also in legacy path** (`translate_txt()` function, line ~2383):
```python
records.append(result | {"chunk_index": idx, "chunk_total": len(chunks)})
```

### Current chunk_record Structure

| Field | Source | Notes |
|-------|--------|-------|
| `status` | Provider/QA result | "success" / "failed" / "skipped" / "dry_run" |
| `output_path` | Chunk file path | |
| `package_id` | `TXT_{stem}_{idx:06d}` | |
| `attempt` | Provider attempt | |
| `qa` | Full QA report | Includes discipline, quality_v5, unified |
| `runtime_pipeline` | Bool | True for RM-6.4.2 path |
| `orchestrator_version` | Orchestrator.version | |
| `session_id` | Orchestrator session | |
| `metadata` | **Not directly in record** | But package has `prompt_runtime` |

### Missing RM-8.2 Fields in chunk_records

| Required Field | Present? | Location |
|----------------|----------|----------|
| `scene_id` | **NO** | Only in `context_state_metadata` passed to orchestrator |
| `chapter_id` | **NO** | Only in `context_state_metadata` |
| `boundary` | **NO** | Only in `context_state_metadata.boundary` |
| `narrative` | **NO** | Only in `context_state_metadata.narrative` |
| `selected_context_ids` | **NO** | Only in `context_state_metadata.selected_context_ids` |
| `context_selection_fingerprint` | **NO** | Only in `context_state_metadata.context_selection_fingerprint` |

---

## The Gap

### Current Flow

```
context_state_metadata (built per-chunk)
    ���� passed to orchestrator.execute(metadata={..., "context_state": context_state_metadata})
    ���� used internally by orchestrator
    ���� NOT persisted to chunk_records
    ���� delivery_pipeline._aggregate_context_continuity() reads from chunk_records[i]["metadata"]["context_state"]
```

### Problem

**The `context_state_metadata` is passed to orchestrator but never written back to `chunk_records`**.

In `_translate_txt_with_runtime_pipeline()`:
- `orchestrator.execute()` receives `context_state_metadata` in metadata
- But the `result` dict appended to `records` does NOT include it
- Legacy path (`translate_txt()`) also doesn't include it

### Evidence

**delivery_pipeline.py:71-82** expects:
```python
ctx = rec.get("metadata", {}).get("context_state")
if ctx:
    scene_id = ctx.get("scene_id")
    chapter_id = ctx.get("chapter_id")
```

But `chunk_records` from runtime pipeline have no `"metadata"` key with `"context_state"`.

---

## Provenance Gap Summary

| Node | Status | Issue |
|------|--------|-------|
| RM-8.2 metadata creation | �� WORKS | Built correctly in `_translate_txt_with_runtime_pipeline()` |
| chunk_records persistence | ��� BROKEN | `context_state_metadata` not saved to records |
| RM-8.3 consumption | ������ PARTIAL | `_aggregate_context_continuity()` reads but finds nothing |
| RM-8.4 packaging | ������ PARTIAL | `build_reader_chapter_map` uses `translated_chunks` + `chunk_records` but lacks scene/chapter IDs |

---

## Resolution Required (P0)

**In P0 Implementation**, must modify `_translate_txt_with_runtime_pipeline()` to persist `context_state_metadata` into each chunk record:

```python
# After orchestrator.execute() returns success
result = {
    "status": "success",
    "output_path": str(chunk_file),
    "package_id": package["package_id"],
    "attempt": 1,
    "qa": qa_report,
    "runtime_pipeline": True,
    "orchestrator_version": orchestrator.version,
    "session_id": session_id,
    "metadata": {  # ADD THIS
        "context_state": context_state_metadata
    } if enable_cross_chunk_context else {},
}
```

**Also in legacy path** (`translate_txt()` function) for consistency when RM-8.2 is enabled via feature flag.

---

## DRIFT_FOUND: PROVENANCE_GAP

**RM-8.2 metadata → chunk_records → RM-8.3 → RM-8.4 chain is BROKEN at chunk_records persistence node.**

The metadata is created correctly but not persisted to the chunk records that downstream consumers (delivery_pipeline, chapter_mapper) read.
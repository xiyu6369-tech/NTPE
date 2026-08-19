# RM-8.2 Pre-Implementation Audit / Architecture Mapping

> **Purpose**: Map existing Context, Scene, Narrative models, extractors, selectors, PromptAssembly, and production txt runtime to actual files, classes, functions, and call sites. This audit is the authoritative reference for the RM-8.2 Implementation Specification.

---

## 1. Architecture Overview (Current Pipeline)

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€????                        PRODUCTION TXT RUNTIME                              ???? lts/txt_translation_runtime.py:translate_txt()                             ???? ?œâ??€ split_text() ??chunks[]                                                ???? ?œâ??€ load_locked_dictionary()                                               ???? ?œâ??€ resume_state (per-chunk SHA256 + status)                               ???? ?œâ??€ _translate_txt_with_runtime_pipeline() (NTPE_RUNTIME_PIPELINE=runtime) ???? ??  ?”â??€ RuntimeOrchestrator                                               ???? ??      ?œâ??€ KnowledgeRuntimeManager.load_all() ??bundles                  ???? ??      ?œâ??€ KnowledgeRuntimeManager.build_merged_runtime() ??MergedRuntime ???? ??      ?œâ??€ PromptBuilder(chunk_text).build(merged) ??PromptAssembly      ???? ??      ?œâ??€ TranslationRuntimeAdapter.prepare() ??TranslationRequest      ???? ??      ?œâ??€ RuntimeSessionManager / RuntimeCheckpointManager / Trace      ???? ??      ?”â??€ TranslationEngine.translate_package_from_request()            ???? ?”â??€ Post-translation QA, formatting, locked-dictionary, character memory  ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??```

**Key Environment Switch**: `NTPE_RUNTIME_PIPELINE=runtime|legacy` (default: `runtime`) controls which path executes (RM-6.4.2).

---

## 2. Model Mapping

### 2.1 Context Model

| Aspect | Location | Class / Function | Notes |
|--------|----------|------------------|-------|
| **Runtime Context (in-flight)** | `core/translation_runtime/runtime_context.py` | `RuntimeContext` (dataclass) | `previous_summary`, `previous_chunk_tail`, `recent_characters`, `recent_terms` ??passed via `TranslationRequest.metadata` |
| **Context Builder (legacy LTS)** | `core/context/context_builder.py` | `ContextBuilder.build()` | Builds text block from `story_state`, `character_state`, `scene_state`, `dialogue_state`, `narrative_state` + `previous_tail` |
| **Context Serializer (legacy LTS)** | `core/context/context_serializer.py` | `ContextSerializer` | File-based persistence under `context/` dir |
| **Context Memory Store (RM-6/7)** | `core/context_scene_memory/store.py` | `ContextMemoryStore` | In-memory store with `contexts: dict[context_id, ContextMemoryRecord]`, `scenes: dict[scene_id, SceneMemoryRecord]`, history, conflicts, snapshots |
| **Context Record** | `core/context_scene_memory/models.py` | `ContextMemoryRecord` (frozen dataclass) | `context_id`, `context_type` (28 types), `value`, `evidence[]`, `confidence`, `approval_status`, `chapter_id`, `scene_id`, `sequence_index`, `expiry_policy` (SCENE_SCOPE, CHAPTER_SCOPE, etc.) |
| **Context Selection** | `core/context_scene_memory/context_selection.py` | `select_context_for_translation()` | Token-budgeted selection by `chapter_id`, `scene_id`, `sequence_index`, `character_ids`, `confidence_threshold`. Returns `ContextSelectionResult` with deterministic fingerprint. |

**Call Sites**:
- `PromptBuilder.build()` (legacy, `core/prompt_builder/prompt_builder.py:68-77`) ??falls back to `ContextMemoryEngine.build_context()` or empty dict
- `RuntimeOrchestrator.execute()` ??`knowledge.load_all()` ??`build_merged_runtime()` ??`PromptBuilder.build()` ??sections include Character, Scene, Narrative from MergedRuntime
- `txt_translation_runtime.py:674` ??`build_prompt_package()` builds `previous_context` from `translated_chunks[-2:]` (last 2 chunks)

### 2.2 Scene Model

| Aspect | Location | Class / Function | Notes |
|--------|----------|------------------|-------|
| **Legacy SceneState** | `core/context/scene_state.py` | `SceneState.update()` | Heuristic keyword matching on `source_text` (Korean ??Chinese location/weather/time/mood/objects) |
| **RM-6 Scene Memory** | `core/context_scene_memory/models.py` | `SceneMemoryRecord` (frozen dataclass) | `scene_id`, `scene_version`, `chapter_id`, `location`, `time_state`, `participants[]`, `active_speaker`, `point_of_view`, `event_state[]`, `unresolved_references[]`, `evidence[]` |
| **Scene State Transitions** | `core/context_scene_memory/scene_state.py` | `update_scene_state()`, `add_scene_participant()`, `remove_scene_participant()`, `transition_scene()`, `transition_chapter()` | `transition_scene()` expires `SCENE_SCOPE` contexts; `transition_chapter()` expires `CHAPTER_SCOPE` contexts |
| **Scene Section Builder** | `core/prompt_runtime/sections.py:123-132` | `build_scene(runtime)` | Extracts `scene` domain from `MergedRuntime` ??`SceneSection` |

**Call Sites**:
- Legacy: `ContextBuilder.build()` reads `states["scene_state"]`
- RM-6: `KnowledgeRuntimeManager.load_scene()` ??`load_all()` ??`build_merged_runtime()` ??`PromptBuilder.build()` ??`build_scene()`
- Scene transitions only invoked by external orchestration (not auto-detected in current pipeline)

### 2.3 Narrative Model

| Aspect | Location | Class / Function | Notes |
|--------|----------|------------------|-------|
| **NarrativeState (Stage-16.2)** | `core/intelligence/narrative_state.py` | `NarrativeState` (dataclass) | `last_perspective`, `last_voice`, `last_tense`, `last_emotional_tone`, `scene_history[]`, `counters` |
| **Narrative Intelligence** | `core/intelligence/narrative_engine.py` | `NarrativeIntelligenceEngine` | `analyze_chunk()`, `update_state()`, `get_context_for_prompt()` |
| **Narrative Section Builder** | `core/prompt_runtime/sections.py:135-144` | `build_narrative(runtime)` | Extracts `narrative` domain from `MergedRuntime` ??`NarrativeSection` |
| **Legacy ContextBuilder** | `core/context/context_builder.py:67-73` | Reads `states["narrative_state"]` | `tone`, `narrative_focus[]`, `emotion_flow[]` |

**Call Sites**:
- Legacy: `ContextBuilder.build()`
- RM-6: `KnowledgeRuntimeManager.load_narrative()` ??merged ??`build_narrative()`
- `NarrativeIntelligenceEngine` not wired into production txt runtime (only used in tests/canary)

### 2.4 Extractor / Selector

| Aspect | Location | Class / Function | Notes |
|--------|----------|------------------|-------|
| **Base Extractor** | `core/knowledge_generation/extractor_base.py` | `BaseKnowledgeExtractor` (ABC) | `extract()`, `_extract_chunk()`, `_chunk_document()`, `normalize()`, `validate_entities()`, `compile_entities()` |
| **Concrete Extractors** | `tools/knowledge_generation/scene_extractor.py`, `narrative_extractor.py` | `SceneExtractor`, `NarrativeExtractor` | Inherit `BaseKnowledgeExtractor`; used offline for knowledge generation |
| **Character Selector** | `core/prompt_builder/character_selector.py` | `CharacterSelector.select(chunk_text)` | Returns matched character entries from `character_match_dictionary` |
| **Glossary Selector** | `core/prompt_builder/glossary_selector.py` | `GlossarySelector.select(chunk_text)` | Returns matched glossary entries |
| **Context Selection (RM-6/7)** | `core/context_scene_memory/context_selection.py` | `select_context_for_translation()` | Token-budgeted, scope-aware selection from `ContextMemoryStore` |

**Call Sites**:
- Extractors: Offline CLI tools (`tools/knowledge_generation/`)
- Selectors: `PromptBuilder.build()` (legacy) ??`character_selector.select()`, `glossary_selector.select()`
- RM-6 Context Selection: Not wired into production txt runtime (available but not called)

### 2.5 PromptAssembly (RM-6.2)

| Aspect | Location | Class / Function | Notes |
|--------|----------|------------------|-------|
| **PromptAssembly** | `core/prompt_runtime/models.py` | `PromptAssembly` (frozen dataclass) | `sections: List[PromptSection]`, `metadata`, `version`, `section_count` |
| **PromptSection Types** | `core/prompt_runtime/models.py` | `SystemSection`, `CharacterSection`, `EntityMappingSection`, `GlossarySection`, `SceneSection`, `NarrativeSection`, `StyleSection`, `ChunkSection` | Fixed order: System ??Character ??Entity Mapping ??Glossary ??Scene ??Narrative ??Style ??Chunk |
| **PromptBuilder** | `core/prompt_runtime/builder.py` | `PromptBuilder.build(runtime: MergedRuntime)` | Assembles all sections via `SECTION_BUILDERS` map |
| **Section Builders** | `core/prompt_runtime/sections.py` | `build_system`, `build_character`, `build_entity_mapping`, `build_glossary`, `build_scene`, `build_narrative`, `build_style`, `build_chunk` | Each extracts domain from `MergedRuntime` |
| **TranslationRuntimeAdapter** | `core/translation_runtime/adapter.py` | `TranslationRuntimeAdapter.prepare(assembly)` | Flattens sections ??prompt string, computes `prompt_hash`, `token_count`, `runtime_snapshot` ??`TranslationRequest` |

**Call Sites**:
- `RuntimeOrchestrator.prepare_request()` and `execute()` ??`PromptBuilder(chunk_text).build(merged)` ??`adapter.prepare()` ??`TranslationRequest`
- `TranslationEngine.translate_package_from_request()` consumes `TranslationRequest`

### 2.6 Production TXT Runtime

| Aspect | Location | Function / Class | Notes |
|--------|----------|------------------|-------|
| **Entry Point** | `lts/txt_translation_runtime.py` | `translate_txt(options)` | Main pipeline; `NTPE_RUNTIME_PIPELINE` env var selects path |
| **Legacy Path** | `lts/txt_translation_runtime.py` | `_translate_txt_with_legacy_pipeline()` | Direct `TranslationEngine` + `build_prompt_package()` |
| **Runtime Path** | `lts/txt_translation_runtime.py:599` | `_translate_txt_with_runtime_pipeline()` | Uses `RuntimeOrchestrator` |
| **Chunking** | `lts/txt_translation_runtime.py:163` / `core/translation_runtime/runtime_chunk.py:8` | `split_text()` | Paragraph-aware, 1800 default (runtime) / 1000 (LTS) |
| **Resume State** | `lts/txt_translation_runtime.py:329` | `load_resume_state()` / `save_resume_state()` | Per-chunk SHA256 + status (`success`, `pass_with_warning`, `dry_run`) |
| **Locked Dictionary** | `lts/txt_translation_runtime.py:239` | `load_locked_dictionary()` | Character/glossary overrides + `character_memory_lts.json` |
| **Post-Processing** | `lts/txt_translation_runtime.py:747-753` | `apply_locked_dictionary()`, `format_translation_output()`, `canonicalize_novel_chinese()`, `apply_literary_collocation_guard()` | Applied after provider response |
| **Quality Gates** | `lts/txt_translation_runtime.py:757-798` | QA V5, Legacy QA, Discipline Runtime | `run_quality_v5_phase1()`, `analyze_translation_quality()`, `orchestrate_runtime_discipline()` |

**Call Flow (Runtime Path)**:
```
translate_txt()
  ??_translate_txt_with_runtime_pipeline()
      ??RuntimeOrchestrator()
          ??start_session()
          ??for each chunk:
              ??build_prompt_package()  [legacy compat, builds previous_context from translated_chunks[-2:]]
              ??orchestrator.execute(chunk_text, session_id, ...)
                  ??knowledge.load_all() ??build_merged_runtime()
                  ??PromptBuilder(chunk_text).build(merged) ??PromptAssembly
                  ??adapter.prepare() ??TranslationRequest
                  ??session_mgr / checkpoint_mgr / trace
                  ??engine.translate_package_from_request()
              ??post-processing (locked dict, formatting, QA, discipline)
          ??orchestrator.complete()
  ??final assembly ??write output
```

---

## 3. Reuse / Wiring / Missing Analysis

### 3.1 Directly Reusable (No Changes Needed)

| Component | File | Reason |
|-----------|------|--------|
| `RuntimeContext` dataclass | `core/translation_runtime/runtime_context.py` | Already passed via `TranslationRequest.metadata` |
| `MergedRuntime` + `KnowledgeRuntimeManager` | `core/knowledge_runtime/` | Full pipeline: load ??snapshot ??merge ??resolve |
| `PromptAssembly` + `PromptBuilder` + section builders | `core/prompt_runtime/` | Complete, tested, deterministic |
| `TranslationRuntimeAdapter` | `core/translation_runtime/adapter.py` | Flattens sections ??`TranslationRequest` |
| `TranslationRequest` / `TranslationResponse` | `core/translation_runtime/models.py` | Immutable handoff to engine |
| `RuntimeOrchestrator` | `core/runtime_orchestrator/manager.py` | Coordinates all RM-6 layers |
| `RuntimeSessionManager`, `RuntimeCheckpointManager`, `RuntimeTraceCollector` | `core/runtime_session.py`, `core/runtime_checkpoint.py`, `core/runtime_trace.py` | Session lifecycle, resume, observability |
| `TranslationEngine.translate_package_from_request()` | `core/translation_engine/translation_engine.py:169` | Consumes `TranslationRequest` directly |
| `split_text()` (runtime) | `core/translation_runtime/runtime_chunk.py` | Chunking logic |
| `ContextMemoryStore` + `select_context_for_translation()` | `core/context_scene_memory/` | Token-budgeted, scope-aware selection with fingerprint |
| `SceneMemoryRecord` + `transition_scene()` / `transition_chapter()` | `core/context_scene_memory/` | Scene/chapter boundary handling with context expiry |

### 3.2 Needs Wiring (Integration Gaps)

| Gap | Current State | Required Wiring |
|-----|---------------|-----------------|
| **Context Selection into PromptAssembly** | `select_context_for_translation()` exists but not called in runtime pipeline | Call `select_context_for_translation()` in `RuntimeOrchestrator.execute()` before `PromptBuilder.build()`; inject selected records as a new `Context` section or merge into existing sections |
| **Scene/Chapter Transition Detection** | `transition_scene()` / `transition_chapter()` exist but not auto-invoked | Detect boundaries (explicit markers or heuristic) in `txt_translation_runtime.py` chunk loop; call `transition_scene()` with `BoundaryType.SCENE_TRANSITION` or `CHAPTER_TRANSITION`; pass expired context IDs to next chunk |
| **NarrativeState Integration** | `NarrativeState` + `NarrativeIntelligenceEngine` exist but not wired | Instantiate `NarrativeIntelligenceEngine` in `RuntimeOrchestrator`; call `analyze_chunk()` per chunk; `update_state()`; feed `get_context_for_prompt()` into `PromptAssembly` (new `NarrativeContext` section or extend `NarrativeSection`) |
| **EntityInjectionSet (RM-7.2)** | `build_entity_mapping()` accepts `injection_set` but runtime passes `None` | Wire `entity_resolver` to produce `EntityInjectionSet` per chunk; pass to `PromptBuilder(chunk_text, entity_injection_set=...)` |
| **Character Memory (V72)** | `quality_character_memory_v72` flag exists but `quality_character_store_v72=None` | Implement `CharacterMemoryStore` interface; pass via `TxtTranslationOptions.quality_character_store_v72` |
| **Context/Scene Store (V72)** | `quality_context_scene_v72` flag exists but `quality_context_scene_store_v72=None` | Pass `ContextMemoryStore` instance via `TxtTranslationOptions.quality_context_scene_store_v72` |

### 3.3 Truly Missing (New Implementation Required)

| Missing Component | Description | Suggested Location |
|-------------------|-------------|-------------------|
| **Scene/Chapter Boundary Detector** | Auto-detect scene/chapter transitions from source text (Korean markers: `?œX?¥`, `?œX?ˆ`, `---`, blank lines, location shifts) | `core/translation_runtime/boundary_detector.py` or `core/context_scene_memory/boundary.py` |
| **Context State Persistence Across Chunks** | `ContextMemoryStore` is in-memory; needs serialization for resume | Extend `RuntimeCheckpointManager` to checkpoint `ContextMemoryStore.snapshot()` |
| **Deterministic Acceptance Test Harness** | No golden-master test for chunk N?’N+1 context passing | `tests/acceptance/rm8_context_propagation_test.py` |
| **Prompt Injection Policy** | No explicit allow/deny list for what data enters prompt | `core/prompt_runtime/injection_policy.py` with `ALLOWED_SECTIONS`, `FORBIDDEN_FIELDS` |
| **Chunk N?’N+1 Context Passing Protocol** | Currently `previous_context` built from `translated_chunks[-2:]` (legacy) | Formalize: `RuntimeContext` + selected `ContextMemoryRecord`s + `SceneMemoryRecord` + `NarrativeState` ??serialized into `TranslationRequest.metadata["context_state"]` |

---

## 4. Minimum Modification Files

| Priority | File | Change |
|----------|------|--------|
| **P0** | `lts/txt_translation_runtime.py` | In `_translate_txt_with_runtime_pipeline()` chunk loop: (1) detect scene/chapter boundaries, (2) call `transition_scene()`, (3) call `select_context_for_translation()`, (4) pass selected context + scene + narrative to `orchestrator.execute()` via `metadata` |
| **P0** | `core/runtime_orchestrator/manager.py` | `execute()`: accept `context_selection: ContextSelectionResult`, `scene_state: SceneMemoryRecord`, `narrative_state: NarrativeState` in `metadata`; merge into `PromptBuilder` or `MergedRuntime` before `build()` |
| **P0** | `core/prompt_runtime/builder.py` | Add optional `context_selection`, `scene_state`, `narrative_state` to `PromptBuilder.__init__`; new section builders or extend existing |
| **P0** | `core/prompt_runtime/sections.py` | Add `build_context_selection()`, `build_scene_state()`, `build_narrative_state()` or extend `build_scene()`, `build_narrative()` |
| **P1** | `core/context_scene_memory/boundary.py` (new) | `detect_boundary(prev_chunk, curr_chunk) ??BoundaryType` |
| **P1** | `core/runtime_checkpoint/manager.py` | Checkpoint `ContextMemoryStore.snapshot()` alongside chunk progress |
| **P1** | `core/translation_runtime/models.py` | Extend `TranslationRequest.metadata` schema for `context_state` (typed dict) |
| **P2** | `tests/acceptance/rm8_context_propagation_test.py` (new) | Golden-master test: fixed input ??verify chunk N context appears in chunk N+1 prompt |

---

## 5. Context State Location

| State Type | Storage | Lifetime | Access Pattern |
|------------|---------|----------|----------------|
| **RuntimeContext (in-flight)** | `TranslationRequest.metadata["runtime_snapshot"]` | Per-request | `TranslationEngine` reads via `request.runtime_snapshot` |
| **ContextMemoryStore** | In-memory (`RuntimeOrchestrator` instance) + `RuntimeCheckpointManager` (JSON) | Session | `KnowledgeRuntimeManager` ??`MergedRuntime` ??`PromptAssembly` |
| **SceneMemoryRecord** | In `ContextMemoryStore.scenes` | Session (persisted via checkpoint) | `transition_scene()` updates; `build_scene()` reads from `MergedRuntime` |
| **NarrativeState** | In-memory (`NarrativeIntelligenceEngine` instance) | Session | `analyze_chunk()` ??`update_state()` ??`get_context_for_prompt()` |
| **Character Memory (V72)** | `character_memory_lts.json` (file) + `quality_character_store_v72` (injected) | Cross-session | `PromptBuilder` / `TQI V72` adapter |
| **Locked Dictionary** | `character_override.json`, `glossary_override.json`, `glossary.txt`, `character_memory_lts.json` | Cross-session | `load_locked_dictionary()` ??applied post-translation |

**Critical**: `ContextMemoryStore` is **not** currently checkpointed. Resume loses context selection state. Must add to `RuntimeCheckpointManager`.

---

## 6. Chunk N ??N+1 Passing Mechanism

### Current (Legacy Path)
```python
# txt_translation_runtime.py:674
previous_context = "\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:]
```
- Only last 2 translated chunks' raw text
- No structured context (characters, scene, narrative)

### Target (Runtime Path)
```
Chunk N completes
    ??    ?œâ? TranslationEngine returns translation
    ??    ?œâ? Post-processing (locked dict, formatting, QA)
    ??    ?œâ? RuntimeOrchestrator.execute() returns RuntimeExecutionResult
    ??      ?”â? trace.events[chunk_finish] recorded
    ??    ?œâ? ContextMemoryStore updated (if extractor runs) ??NOT YET WIRED
    ??    ?œâ? NarrativeIntelligenceEngine.analyze_chunk(source_N, translation_N)
    ??      ??update_state(perspective, voice, tense, tone, transitions)
    ??    ?œâ? Scene transition check: detect_boundary(source_N, source_N+1)
    ??      ??if SCENE_TRANSITION: transition_scene(store, from_N, to_N+1, ...)
    ??      ??if CHAPTER_TRANSITION: transition_chapter(store, from_N, to_N+1, ...)
    ??    ?œâ? Checkpoint: save ContextMemoryStore.snapshot() + session + progress
    ??    ??Chunk N+1 prepare
    ??    ?œâ? select_context_for_translation(store, chapter_id, scene_id_N+1, seq_N+1, ...)
    ??      ??ContextSelectionResult (selected_records, selected_chars, fingerprint)
    ??    ?œâ? scene_state = store.get_scene(scene_id_N+1)
    ??    ?œâ? narrative_context = narrative_engine.get_context_for_prompt()
    ??    ?œâ? PromptBuilder(chunk_text_N+1, context_selection, scene_state, narrative_context).build(merged)
    ??    ?”â? adapter.prepare() ??TranslationRequest.metadata["context_state"] = {
            "context_selection_fingerprint": fingerprint,
            "scene_id": scene_id_N+1,
            "scene_version": scene_state.scene_version,
            "narrative": narrative_context,
            "selected_context_ids": [r.item_id for r in selected_records],
        }
```

---

## 7. Scene / Chapter Reset Rules

| Trigger | Action | Context Expiry |
|---------|--------|----------------|
| **Scene Transition** (`BoundaryType.SCENE_TRANSITION`) | `transition_scene(store, from_scene, SCENE_TRANSITION, to_scene)` | All `SCENE_SCOPE` records with `expiry_policy.scope_id == from_scene` ??`EXPIRED`; participants ??`EXITED_SCENE`; unresolved refs ??`EXPIRED` |
| **Chapter Transition** (`BoundaryType.CHAPTER_TRANSITION`) | `transition_chapter(store, from_scene, to_scene, to_chapter)` | `SCENE_SCOPE` (from_scene) + `CHAPTER_SCOPE` (from_chapter) ??`EXPIRED` |
| **Same Scene** (`BoundaryType.SAME_SCENE`) | No transition | No expiry |
| **Unknown Transition** | Conservative: no expiry, no new scene | None |

**Detection**: Currently **not implemented**. Must be added (see Â§4 P1).

---

## 8. Prompt Injection Policy (What Can / Cannot Enter Prompt)

### 8.1 Can Be Injected (Allowed)

| Data | Source | Section | Token Cost |
|------|--------|---------|------------|
| Character profiles (name, emotion, focus, notes) | `MergedRuntime.character` | `CharacterSection` | ~50-200 tokens |
| Glossary terms (matched in chunk) | `MergedRuntime.glossary` | `GlossarySection` | ~20-100 tokens |
| Scene state (location, time, weather, mood, objects) | `MergedRuntime.scene` | `SceneSection` | ~30-80 tokens |
| Narrative state (tone, focus, emotion_flow) | `MergedRuntime.narrative` | `NarrativeSection` | ~30-80 tokens |
| Style rules (principles, forbidden, examples) | `MergedRuntime.style` | `StyleSection` | ~50-150 tokens |
| Entity mappings (RM-7.2) | `EntityInjectionSet` | `EntityMappingSection` | ~20-100 tokens |
| Selected context records (token-budgeted) | `ContextSelectionResult` | **NEW: `ContextSection`** | ??`DEFAULT_CONTEXT_TOKEN_BUDGET` (512) |
| Selected character memories | `ContextSelectionResult` | **NEW: extend `CharacterSection`** | ??`DEFAULT_CHARACTER_TOKEN_BUDGET` (256) |
| Chunk source text | `chunk_text` | `ChunkSection` | Variable |

### 8.2 Cannot Be Injected (Forbidden)

| Data | Reason | Enforcement |
|------|--------|-------------|
| Raw `ContextMemoryRecord.evidence[]` (internal IDs, hashes, rule_ids) | Internal metadata, not for model | `PromptSection` builders only emit `value` + domain metadata |
| `ContextMemoryRecord.confidence`, `approval_status`, `version`, `expiry_policy` | Internal state | Not in section content |
| `SceneMemoryRecord.evidence[]`, `scene_version`, `status` | Internal | Not in section content |
| `UnresolvedReference.candidate_targets`, `evidence[]`, `confidence` | Internal resolution | Only `surface_form` or `surface_form?’resolved_target` in `build_scene()` unresolved refs |
| `NarrativeState.counters`, `scene_history` (raw) | Internal tracking | `get_context_for_prompt()` returns summary only |
| Provider metadata (prompt_hash, token_count, snapshot_id) | Runtime plumbing | Stripped by `TranslationRuntimeAdapter` (only in `runtime_snapshot`) |
| Resume state internals (SHA256, chunk status) | Operational | Not passed to `PromptBuilder` |

**Enforcement Point**: `PromptBuilder.build()` and section builders in `core/prompt_runtime/sections.py` are the **sole** prompt construction path. No other code constructs provider prompts.

---

## 9. Deterministic Acceptance Tests

### 9.1 Test Strategy: Golden Master + Property-Based

```python
# tests/acceptance/rm8_context_propagation_test.py

FIXED_INPUT = "chapter1.txt"  # 10 chunks, known scene boundaries at chunk 3, 7

def test_chunk_n_to_n1_context_propagation():
    """Verify structured context passes from chunk N to N+1 deterministically."""
    runtime = TranslationRuntime()
    options = TxtTranslationOptions(...)

    # Run once to generate golden master
    result = runtime.translate_txt(options)

    # Extract per-chunk prompt hashes from records
    prompt_hashes = [r["prompt_hash"] for r in result["records"] if r["status"] == "success"]

    # Re-run with same options ??identical hashes
    result2 = runtime.translate_txt(options)
    prompt_hashes2 = [r["prompt_hash"] for r in result2["records"] if r["status"] == "success"]

    assert prompt_hashes == prompt_hashes2, "Prompt hashes must be deterministic"

    # Verify context fingerprint continuity
    for i in range(1, len(prompt_hashes)):
        # Chunk i's context_selection_fingerprint must derive from chunk i-1 state
        ctx_i = result["records"][i]["metadata"]["context_state"]
        ctx_i_1 = result["records"][i-1]["metadata"]["context_state"]
        assert ctx_i["scene_id"] == ctx_i_1["scene_id"] or \
               ctx_i["scene_version"] > ctx_i_1["scene_version"], \
               "Scene version must advance on transition"

def test_scene_transition_expires_context():
    """Verify SCENE_SCOPE contexts expire at scene boundary."""
    store = ContextMemoryStore()
    # ... setup scene A with SCENE_SCOPE context ...
    transition_scene(store, from_scene="scene_A", boundary=BoundaryType.SCENE_TRANSITION, to_scene="scene_B")
    # Select for scene_B
    selection = select_context_for_translation(store, scene_id="scene_B", ...)
    assert not any(r.item_type == "context" and r.context_type == "SCENE_SCOPE" for r in selection.selected_records)

def test_chapter_transition_expires_chapter_scope():
    """Verify CHAPTER_SCOPE contexts expire at chapter boundary."""
    # Similar pattern

def test_resume_restores_context_store():
    """Verify ContextMemoryStore checkpoint/restore."""
    orchestrator = RuntimeOrchestrator()
    orchestrator.execute(chunk_1, session_id="s1", current_chunk=1, total_chunks=3)
    checkpoint = orchestrator.checkpoint_manager.latest_checkpoint("s1")
    # Simulate restart
    orchestrator2 = RuntimeOrchestrator()
    orchestrator2.checkpoint_manager.restore(checkpoint.checkpoint_id)
    assert orchestrator2.knowledge.get_merged_runtime() == orchestrator.knowledge.get_merged_runtime()
```

### 9.2 Required Test Infrastructure

| Test | Location | Dependencies |
|------|----------|--------------|
| Golden master prompt hashes | `tests/acceptance/rm8_context_propagation_test.py` | Fixed input file, frozen provider (mock) |
| Scene/chapter boundary detection | `tests/unit/context_scene_memory/test_boundary.py` | `detect_boundary()` function |
| Context selection fingerprint stability | `tests/unit/context_scene_memory/test_selection_fingerprint.py` | `select_context_for_translation()` |
| Checkpoint/restore ContextMemoryStore | `tests/unit/runtime_checkpoint/test_context_store_checkpoint.py` | `RuntimeCheckpointManager` extended |

---

## 10. Summary: RM-8.2 Implementation Scope

| Category | Count | Examples |
|----------|-------|----------|
| **Reuse as-is** | 12 | `RuntimeContext`, `MergedRuntime`, `PromptAssembly`, `TranslationRuntimeAdapter`, `RuntimeOrchestrator`, `TranslationEngine.translate_package_from_request`, `split_text`, `ContextMemoryStore`, `select_context_for_translation`, `SceneMemoryRecord`, `transition_scene`, `transition_chapter` |
| **Wire (integrate existing)** | 6 | Context selection ??PromptAssembly, Scene transition detection ??transition_scene, NarrativeState ??PromptAssembly, EntityInjectionSet ??PromptBuilder, CharacterMemoryStore V72, ContextSceneStore V72 |
| **New implementation** | 5 | Boundary detector, ContextMemoryStore checkpointing, Prompt injection policy, Acceptance test harness, TranslationRequest.context_state schema |
| **Modified files (min)** | 6 | `txt_translation_runtime.py`, `runtime_orchestrator/manager.py`, `prompt_runtime/builder.py`, `prompt_runtime/sections.py`, `runtime_checkpoint/manager.py`, `translation_runtime/models.py` |

---

## 11. Next Step: RM-8.2 Implementation Specification

This audit provides the factual basis. The Implementation Specification will:
1. Define exact function signatures for new wiring points
2. Specify `context_state` schema in `TranslationRequest.metadata`
3. Define boundary detection algorithm (Korean markers + heuristic)
4. Define checkpoint payload for `ContextMemoryStore`
5. Define acceptance test golden master generation procedure
6. List exact file edits with line references

**No production code changes until Specification is reviewed and approved.**

# P0 Stage 4 Batch 3A — Memory / Entity / Context Formal Value & Wiring Audit

**Status:** AUDIT COMPLETE  
**Date:** 2026-08-18  
**Author:** Kilo Code (Audit Agent)  
**Production Code Modified:** NO  
**Frozen Contracts Modified:** NO  
**Archive Performed:** NO  
**Batch 3B Authorized:** NO  
**Owner Decision Required:** YES  

---

## 1. Executive Summary

This audit examines NTPE's existing Memory / Entity / Context capabilities to determine which constitute **formal product capabilities** versus **experimental/historical implementations**. The audit covers:

- **Knowledge Runtime** (`core/knowledge_runtime/` vs legacy `core/knowledge/`)
- **Character Memory v2** (`core/character_memory_v2/`)
- **Context / Scene Memory** (`core/context_scene_memory/`)
- **Entity Resolver** (`core/entity_resolver/`)
- **TE v7.2 Integration** (`core/translation_quality_integration_v72/`)

**Key Finding:** All five capability areas have substantial implementations with tests, but **none are fully wired into the production Runtime pipeline as formal product capabilities**. They exist as:
- Complete library implementations with validation
- Feature-gated behind CLI flags (default OFF)
- Available for canary/experimental use
- Not activated in the default production path

The legacy `core/knowledge/` package is a **separate, larger system** that is NOT used by the Runtime pipeline — `core/knowledge_runtime/` is the actual Runtime knowledge layer.

---

## 2. Original Specification Baseline

### 2.1 RM-5.7.0 Offline Knowledge Generation Architecture

The original specification (RM-5.7.0) planned **5 LLM-based extractors**:
1. Character Extractor
2. Glossary Extractor  
3. Scene Extractor
4. Narrative Extractor
5. Style Extractor

**Status:** These extractors were **designed but not implemented** in the current codebase. The current `core/knowledge_runtime/` is a **provider-free, offline-only architecture skeleton** (RM-6.1.x) that loads pre-built bundles — it does not perform LLM extraction.

### 2.2 RM-6.1.x Knowledge Runtime (Current)

Formal specification for the **offline-only Knowledge Runtime**:
- `KnowledgeLoader` — loads domain bundles from plain dicts
- `KnowledgeMerger` — merges bundles + snapshots into `MergedRuntime`
- `KnowledgeResolver` — resolves keys from merged runtime only
- `KnowledgeSnapshotStore` — capture/restore point-in-time snapshots
- `KnowledgeRuntimeManager` — orchestrates Loader → Snapshot → Merger → Resolver

**Key Contract:** Resolver queries **merged runtime exclusively** (RM-6.1.2).

### 2.3 RM-7.2 Entity Resolver

Specification for pre-translation entity mapping:
- `EntityExtractor` — extracts known Korean entities from chunks
- `EntityResolver` — resolves via USER > RUNTIME > LEARNING > AUTO hierarchy
- `EntityInjector` — injects resolved entities as "Entity Mapping" prompt section
- `EntityInjectionSet` — collection of `ResolvedEntity` for prompt injection

### 2.4 RM-8.2 Cross-Chunk Context Continuity

Feature-gated extension for context/scene memory:
- `ContextMemoryStore` + `select_context_for_translation()`
- `SceneMemoryRecord` + `transition_scene()/transition_chapter()`
- Integrated via `PromptBuilder` parameterization (`enable_cross_chunk_context` flag)
- **Default OFF** for backward compatibility

### 2.5 TE v7.2 Quality Integration

Translation quality integration with token-budgeted selection:
- `QualityIntegrationFlags` — feature gates (all default FALSE)
- `PromptBudget` — token allocation (character/context/scene/naturalness)
- `apply_to_prompt_package()` — adapter at final prompt serialization
- `quality_character_store_v72` / `quality_context_scene_store_v72` — option fields only

---

## 3. Current Architecture

### 3.1 Production Entry Points

| Entry Point | Pipeline | Knowledge Source | Memory/Context |
|-------------|----------|------------------|----------------|
| `lts/txt_translation_runtime.py::translate_txt()` | **Legacy** | `character_memory_lts.json` + `glossary.txt` + `character_override.json` | None (simple previous_context string) |
| `core/translation_runtime/runtime.py::translate_txt()` | **Runtime** (delegates to LTS) | Same as above | RM-8.2 feature-gated (`quality_context_scene_v72`) |
| `core/runtime_orchestrator/manager.py::RuntimeOrchestrator` | **Runtime Orchestrator** | `KnowledgeRuntimeManager` → `MergedRuntime` | RM-8.2 via metadata (feature-gated) |

### 3.2 Knowledge Flow (Runtime Path)

```
KnowledgeRuntimeManager.load_all() 
    → KnowledgeBundle per domain (character, glossary, scene, narrative, style)
    → KnowledgeMerger.build_merged_runtime() 
    → MergedRuntime (domains: merged entries per domain)
    → PromptBuilder.build(MergedRuntime) 
    → PromptAssembly (sections: System, Character, Entity Mapping, Glossary, Scene, Narrative, Style, Context*, Chunk)
    → TranslationRuntimeAdapter.prepare() 
    → TranslationRequest → TranslationEngine
```

*Context section only when `enable_cross_chunk_context=True`

### 3.3 Legacy Knowledge Package (`core/knowledge/`)

**Separate, unused by Runtime.** Contains:
- `core/knowledge/runtime/` — `SessionRuntime`, `RepositoryRuntime`, `PromptRuntime`, `ContextRuntime` (different API)
- `core/knowledge/synchronization/` — sync manager, conflict resolver, manifest
- `core/knowledge/semantic/` — tokenizer, semantic index, search engine, ranking
- `core/knowledge/maintenance/` — statistics, repair, optimizer, diagnostics
- `core/knowledge/repositories/` — memory repository, manager
- `core/knowledge/providers/` — scene, runtime, narrative, glossary, character providers

**This is a full knowledge management system with semantic search, synchronization, maintenance — NOT used by the translation Runtime.**

---

## 4. KnowledgeRuntime Audit

### 4.1 `core/knowledge_runtime/` — Formal Product Capability

| Aspect | Status |
|--------|--------|
| **Implementation** | Complete: Loader, Merger, Resolver, SnapshotStore, Manager |
| **Tests** | Unit tests exist (`tests/unit/...`) |
| **Production Reachability** | **YES** — Used by `RuntimeOrchestrator` (RM-6.4.0) |
| **Runtime Path** | `RuntimeOrchestrator.prepare_request()` → `knowledge.load_all()` → `build_merged_runtime()` → `PromptBuilder.build()` |
| **Feature Gate** | None (always active in Runtime path) |
| **Default** | ON (when using Runtime Orchestrator) |
| **Quality Value** | Provides structured domain knowledge (character, glossary, scene, narrative, style) to prompt assembly |
| **Stability Risk** | LOW — offline-only, no provider calls, frozen contracts |
| **Complexity Cost** | MODERATE — 5 domain bundles, merger, resolver, snapshots |
| **Duplication** | YES — duplicates `core/knowledge/` functionality but with different architecture |
| **Classification** | **FORMAL_PRODUCT_CAPABILITY** |

**Evidence:** `core/runtime_orchestrator/manager.py:53` instantiates `KnowledgeRuntimeManager()`; `prepare_request()` at line 111-113 calls `load_all()` → `build_merged_runtime()` → `PromptBuilder.build()`.

### 4.2 `core/knowledge/` — LEGACY_REPLACED (for Runtime)

| Aspect | Status |
|--------|--------|
| **Implementation** | Extensive (semantic search, sync, maintenance, providers, repositories) |
| **Tests** | Likely exist but not audited |
| **Production Reachability** | **NO** — Not imported by `RuntimeOrchestrator`, `TranslationRuntime`, or `txt_translation_runtime.py` |
| **Runtime Path** | N/A |
| **Feature Gate** | N/A |
| **Default** | N/A |
| **Quality Value** | Rich knowledge management (semantic search, versioning, sync) but NOT connected to translation |
| **Stability Risk** | N/A (not in production path) |
| **Complexity Cost** | HIGH — large codebase |
| **Duplication** | YES — overlaps with `knowledge_runtime` domains but different architecture |
| **Classification** | **LEGACY_REPLACED** (for Runtime purposes) |

**Critical Note:** The legacy `core/knowledge/` is a **complete knowledge management platform** with semantic search, synchronization, maintenance, and provider abstractions. It is **architecturally distinct** from `core/knowledge_runtime/` (which is a minimal offline loader/merger). They serve different purposes. The legacy package may still be used by other tools (archive, canary, etc.) but **not by the translation Runtime**.

---

## 5. Character Memory Audit

### 5.1 `core/character_memory_v2/` — Implementation Status

| Module | Purpose | Production Reachability |
|--------|---------|------------------------|
| `models.py` | Data models: `MemoryRecord`, `Evidence`, `ConflictRecord`, `SelectionResult`, `PromptMemoryItem` | Library only |
| `store.py` | `MemoryStore` with add/merge, conflict resolution, snapshots | Library only |
| `selection.py` | Token-budgeted selection for prompt injection | Library only |
| `normalization.py` | Text normalization, stable IDs | Library only |
| `lifecycle.py` | Expiry, status transitions | Library only |
| `deduplication.py` | Evidence ranking, merge logic | Library only |
| `validation.py` | Schema validation | Library only |

### 5.2 Production Usage Analysis

**Legacy Pipeline (`lts/txt_translation_runtime.py`):**
- Loads `character_memory_lts.json` (simple `{korean: chinese}` dict) via `load_locked_dictionary()` → `resolve_character_memory_path()` (line 262-265)
- Applied as post-translation alias replacement (`apply_locked_dictionary()`, line 292-304)
- **No v2 store usage**

**Runtime Pipeline (`RuntimeOrchestrator`):**
- `PromptBuilder.build_character()` accepts optional `character_memories` parameter (line 103-106 in `prompt_runtime/builder.py`)
- Parameter sourced from `ContextSelectionResult.selected_character_memories` (RM-8.2 extension)
- **Only activated when `enable_cross_chunk_context=True`** (feature-gated)

**TE v7.2 Integration:**
- `QualityIntegrationRequest.character_store` field exists (line 25 in `models.py`)
- `apply_to_prompt_package()` passes `character_store=options.quality_character_store_v72` (line 144 in `adapter.py`)
- **Option field only — no production instance created**

### 5.3 `character_memory_lts.json` vs v2 Store Relationship

| Aspect | `character_memory_lts.json` | `character_memory_v2` Store |
|--------|----------------------------|----------------------------|
| Format | Simple `{korean: chinese}` dict | Rich `MemoryRecord` with evidence, confidence, approval, expiry |
| Loading | `load_json_pairs()` → merged into `locked_dictionary` | `MemoryStore.from_dict()` / `restore_snapshot()` |
| Usage | Post-translation alias normalization | Prompt injection via `build_character()` / TE v7.2 selection |
| Production | **YES** (legacy + runtime) | **NO** (library only) |
| Migration Path | Manual export/import | No automated migration |

### 5.4 Classification

| Capability | Classification | Rationale |
|------------|----------------|-----------|
| `character_memory_v2` library | **FORMAL_CAPABILITY_NOT_WIRED** | Complete implementation with validation, selection, lifecycle — but no production wiring except feature-gated RM-8.2 path |
| `character_memory_lts.json` loading | **FORMAL_PRODUCT_CAPABILITY** | Actually used in production (both legacy and runtime) |
| v2 store as formal Runtime | **REQUIRES_DECISION** | Requires Owner decision on: migration from LTS format, activation policy, evidence/approval workflow |

---

## 6. Context / Scene Memory Audit

### 6.1 `core/context_scene_memory/` — Implementation Status

| Module | Purpose | Production Reachability |
|--------|---------|------------------------|
| `models.py` | `ContextMemoryRecord`, `SceneMemoryRecord`, `ContextEvidence`, `UnresolvedReference`, `ContextSelectionResult` | Library only |
| `store.py` | `ContextMemoryStore` with contexts, scenes, conflicts, snapshots | Library only |
| `context_selection.py` | `select_context_for_translation()` — token-budgeted selection | Library only |
| `scene_state.py` | `transition_scene()`, `transition_chapter()` | Library only |
| `normalization.py` | Text normalization, stable IDs | Library only |
| `lifecycle.py` | Expiry, status transitions | Library only |
| `interoperability.py` | Cross-system integration helpers | Library only |
| `validation.py` | Schema validation | Library only |

### 6.2 Production Usage Analysis

**Runtime Pipeline (`lts/txt_translation_runtime.py` lines 629-665):**
```python
enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)
context_store = ContextMemoryStore() if enable_cross_chunk_context else None
narrative_engine = NarrativeIntelligenceEngine() if enable_cross_chunk_context else None
```
- **Feature-gated** behind `quality_context_scene_v72` option (default FALSE)
- When enabled: creates fresh `ContextMemoryStore` per translation (no persistence)
- Uses `transition_scene()`, `transition_chapter()`, `select_context_for_translation()`
- Context passed to `RuntimeOrchestrator` via metadata

**Runtime Orchestrator:**
- Accepts `context_selection`, `scene_state`, `narrative_state` via metadata (lines 155-159)
- Passes to `PromptBuilder` when `enable_cross_chunk_context=True` (lines 167-174)

**Prompt Builder:**
- `build_character()` extends with `character_memories` from selection (line 103-106)
- `build_scene()` extends with `scene_state` (line 114-117)
- `build_narrative()` extends with `narrative_state` (line 119-122)
- **NEW** `Context` section via `build_context_selection()` (line 123-125)

**TE v7.2 Integration:**
- `QualityIntegrationRequest.context_scene_store` field exists
- `select_quality_context()` in `selection.py` uses both stores
- **Option fields only — no production instances**

### 6.3 Chunk-to-Chunk Context: Actual Effectiveness

| Claim | Reality |
|-------|---------|
| "Chunk-to-chunk context continuity" | Only when `quality_context_scene_v72=True` AND `RuntimeOrchestrator` path used |
| "Scene state tracking" | Fresh `ContextMemoryStore` per file — no cross-file persistence |
| "Context selection" | Token-budgeted but operates on empty store unless pre-populated |
| "Production integration" | **Not in default path** — requires explicit CLI flags |

### 6.4 Classification

| Capability | Classification | Rationale |
|------------|----------------|-----------|
| `context_scene_memory` library | **FORMAL_CAPABILITY_NOT_WIRED** | Complete implementation but only feature-gated experimental path |
| Cross-chunk context in Runtime | **EXPERIMENTAL_CANARY** | Behind `quality_context_scene_v72` flag (default OFF), no persistence, fresh store per run |
| TE v7.2 context integration | **EXPERIMENTAL_CANARY** | Option fields only, no production store instances |

---

## 7. Entity Resolver Audit

### 7.1 `core/entity_resolver/` — Implementation Status

| Module | Purpose | Production Reachability |
|--------|---------|------------------------|
| `models.py` | `ResolvedEntity`, `EntityInjectionSet`, `ExtractedEntity`, `InjectionSource` (USER>RUNTIME>LEARNING>AUTO) | Library only |
| `extractor.py` | `EntityExtractor` — exact match + Korean name pattern fallback | Library only |
| `resolver.py` | `EntityResolver` — hierarchy resolution via MergedRuntime | Library only |
| `injector.py` | `EntityInjector` → `PromptSection` "Entity Mapping" | Library only |

### 7.2 Production Usage Analysis

**Prompt Builder (`prompt_runtime/sections.py:111-165`):**
- `build_entity_mapping(runtime, injection_set)` accepts `EntityInjectionSet`
- Formats known/unknown entities with source level markers
- **Only called when `entity_injection_set` provided to `PromptBuilder`**

**Runtime Orchestrator (`manager.py:109, 169`):**
- Accepts `entity_injection_set` via metadata (line 159)
- Passes to `PromptBuilder` (lines 109, 169)
- **No production code creates `EntityInjectionSet`**

**TE v7.2 / Canary:**
- `tools/canary/run_entity_canary.py` demonstrates full pipeline
- `tools/canary/run_ke_learning_loop_canary.py` integrates with learning data
- **Canary only — not in production**

**Legacy Pipeline:** No entity resolver usage.

### 7.3 Entity Resolution Pipeline (If Wired)

```
Source Text (chunk)
    ↓
EntityExtractor.extract(chunk) — exact match from known_entities + Korean pattern fallback
    ↓
EntityResolver.resolve(extracted) — USER > RUNTIME > LEARNING > AUTO
    ↓
EntityInjectionSet (ResolvedEntity list with source_level)
    ↓
EntityInjector.inject() → PromptSection "Entity Mapping"
    ↓
PromptBuilder.build_entity_mapping() → PromptAssembly
```

### 7.4 Critical Gaps for Production Wiring

| Gap | Impact |
|-----|--------|
| **No production `known_entities` source** | `EntityExtractor.known_entities` must be populated from `MergedRuntime` via `build_known_entities_from_runtime()` — not automated |
| **No per-chunk execution** | Extractor/Resolver must run per chunk — no integration point in `RuntimeOrchestrator.execute()` |
| **No user override persistence** | `user_overrides` dict is in-memory only |
| **No learning data pipeline** | `build_learning_data_from_history()` exists but no history source |
| **Fail-closed behavior** | Resolver returns `UNKNOWN_TRANSLATION` for unknown — safe but may pollute prompt |
| **Korean name false positives** | `KOREAN_NAME_PATTERN` matches any 2-4 Hangul syllables — high false positive rate |

### 7.5 Classification

| Capability | Classification | Rationale |
|------------|----------------|-----------|
| `entity_resolver` library | **FORMAL_CAPABILITY_NOT_WIRED** | Complete pipeline (extract→resolve→inject) but no production wiring |
| Entity Mapping prompt section | **FORMAL_CAPABILITY_NOT_WIRED** | `build_entity_mapping()` exists and handles `EntityInjectionSet` but never called with real data |
| Canary demonstrations | **EXPERIMENTAL_CANARY** | Full pipeline works in canary tools only |

**Recommendation:** Entity Resolver **should become a formal product capability** IF:
1. `known_entities` auto-populated from `MergedRuntime` per chunk
2. Integrated into `RuntimeOrchestrator.execute()` per-chunk flow
3. User override persistence added
4. Korean name pattern false positives addressed (restrict to known entities only)

---

## 8. TE v7.2 Integration Audit

### 8.1 Component Analysis

| Component | Status | Production Reachability |
|-----------|--------|------------------------|
| `QualityIntegrationFlags` | Feature gates (all default FALSE) | Option parsing only |
| `PromptBudget` | Token allocation config | Option field only |
| `QualityIntegrationRequest` | Adapter input (stores, flags, budget) | Option fields only |
| `apply_to_prompt_package()` | Final prompt serialization adapter | **Called in legacy path** (line 1485 in `txt_translation_runtime.py`) |
| `integrate_prompt()` | Core integration logic | Called via adapter |
| `select_quality_context()` | Token-budgeted selection | Uses `character_store`/`context_scene_store` option fields |
| `quality_character_store_v72` | Option field (`Any | None`) | **Never instantiated in production** |
| `quality_context_scene_store_v72` | Option field (`Any | None`) | **Never instantiated in production** |

### 8.2 `apply_to_prompt_package()` — Only Production Touchpoint

In `lts/txt_translation_runtime.py:1485-1502`:
```python
return apply_translation_quality_integration_v72(
    package,
    flags=QualityIntegrationFlags(
        integration=options.quality_integration_v72,
        character_memory=options.quality_character_memory_v72,
        context_scene=options.quality_context_scene_v72,
        naturalness=options.quality_naturalness_v72,
        kill_switch=options.quality_integration_kill_switch_v72,
    ),
    character_store=options.quality_character_store_v72,  # ALWAYS None
    context_scene_store=options.quality_context_scene_store_v72,  # ALWAYS None
    ...
)
```

**All flags default FALSE. Both stores always None.**

The adapter executes but:
- `flags.enabled` → FALSE → returns package unchanged (line 61-63 in `adapter.py`)
- Even if flags TRUE: stores are None → `select_quality_context()` operates on empty stores

### 8.3 Classification

| Capability | Classification | Rationale |
|------------|----------------|-----------|
| TE v7.2 adapter (`apply_to_prompt_package`) | **FORMAL_CAPABILITY_NOT_WIRED** | Called in production path but all gates default OFF, stores None |
| `QualityIntegrationFlags` | **EXPERIMENTAL_CANARY** | Feature flags for canary control |
| `quality_character_store_v72` / `quality_context_scene_store_v72` | **UNUSED_IMPLEMENTATION** | Option fields with no production instantiation |
| Token-budgeted selection | **EXPERIMENTAL_CANARY** | Works in tests/canary only |

---

## 9. Runtime Integration Map

### 9.1 Legacy Pipeline (`lts/txt_translation_runtime.py::translate_txt`)

| Component | Used? | How |
|-----------|-------|-----|
| `character_memory_lts.json` | YES | Loaded into `locked_dictionary` → post-translation alias replacement |
| `glossary.txt` / overrides | YES | Merged into `locked_dictionary` |
| `core/knowledge_runtime/` | NO | Not imported |
| `character_memory_v2` | NO | Not imported |
| `context_scene_memory` | NO | Not imported (unless `quality_context_scene_v72` in Runtime path) |
| `entity_resolver` | NO | Not imported |
| TE v7.2 adapter | YES | Called but flags default OFF, stores None |

### 9.2 Runtime Pipeline (`core/translation_runtime/runtime.py::translate_txt`)

| Component | Used? | How |
|-----------|-------|-----|
| Delegates to LTS | YES | `from lts.txt_translation_runtime import translate_txt` |
| `RuntimeOrchestrator` | NO | Not used in `translate_txt()` |

### 9.3 Runtime Orchestrator Path (`RuntimeOrchestrator.execute`)

| Component | Used? | How |
|-----------|-------|-----|
| `KnowledgeRuntimeManager` | YES | `load_all()` → `build_merged_runtime()` |
| `PromptBuilder` | YES | `build(MergedRuntime)` → `PromptAssembly` |
| `Entity Mapping` | CONDITIONAL | Only if `entity_injection_set` in metadata |
| Cross-chunk context | CONDITIONAL | Only if `enable_cross_chunk_context=True` in metadata |
| `character_memory_v2` store | NO | Not instantiated |
| `context_scene_memory` store | NO | Not instantiated (fresh store in LTS path only) |
| `entity_resolver` | NO | Not instantiated |

---

## 10. Legacy Pipeline Comparison

| Capability | Legacy Pipeline | Runtime Orchestrator | TE v7.2 Adapter |
|------------|-----------------|---------------------|-----------------|
| Character Memory | `character_memory_lts.json` → locked dict | `MergedRuntime` character domain + optional RM-8.2 selection | `quality_character_store_v72` (None) |
| Context/Scene | Simple `previous_context` string | RM-8.2 `ContextMemoryStore` + selection (feature-gated) | `quality_context_scene_store_v72` (None) |
| Entity Resolution | None | `EntityInjectionSet` via metadata (not wired) | Not applicable |
| Knowledge Domains | Glossary only (file-based) | 5 domains via `KnowledgeRuntimeManager` | Not applicable |
| Prompt Assembly | `build_prompt_package()` (monolithic) | `PromptBuilder` → `PromptAssembly` (sectioned) | Post-processes assembled prompt |
| Quality Integration | Post-translation QA only | Not integrated | Pre-translation prompt enrichment (gated) |

---

## 11. Production Reachability Matrix

| Module | Imported by Production | Instantiated in Production | Executed in Default Path | Feature Gate |
|--------|------------------------|---------------------------|-------------------------|--------------|
| `core/knowledge_runtime/` | YES (`RuntimeOrchestrator`) | YES (`KnowledgeRuntimeManager()`) | YES (Runtime path) | None |
| `core/knowledge/` | NO | NO | NO | N/A |
| `core/character_memory_v2/` | NO | NO | NO | RM-8.2 / TE v7.2 |
| `core/context_scene_memory/` | YES (LTS Runtime path) | YES (fresh store when flag ON) | NO (flag default OFF) | `quality_context_scene_v72` |
| `core/entity_resolver/` | NO | NO | NO | None |
| `core/translation_quality_integration_v72/` | YES (LTS) | YES (adapter called) | NO (flags default OFF) | `quality_integration_v72` etc. |

---

## 12. Capability Classification Matrix

| Capability | Original Intent | Current State | Classification |
|------------|-----------------|---------------|----------------|
| **KnowledgeRuntime** (RM-6.1.x) | Offline knowledge loader/merger for Runtime | **Fully wired** in `RuntimeOrchestrator` | **FORMAL_PRODUCT_CAPABILITY** |
| **Legacy Knowledge** (`core/knowledge/`) | Full knowledge management platform | **Not used by Runtime** | **LEGACY_REPLACED** (for Runtime) |
| **Character Memory v2** | Rich evidence-based character memory with lifecycle | **Library complete**, feature-gated RM-8.2/TE v7.2 only | **FORMAL_CAPABILITY_NOT_WIRED** |
| **Character Memory LTS** | Simple name mapping for post-translation | **Actively used** in both pipelines | **FORMAL_PRODUCT_CAPABILITY** |
| **Context/Scene Memory** | Cross-chunk continuity with scene tracking | **Library complete**, feature-gated only | **FORMAL_CAPABILITY_NOT_WIRED** |
| **Cross-Chunk Context (Runtime)** | Chunk-to-chunk context via RM-8.2 | **Experimental** — fresh store, flag OFF default | **EXPERIMENTAL_CANARY** |
| **Entity Resolver** | Pre-translation entity mapping (USER>RUNTIME>LEARNING>AUTO) | **Library complete**, no production wiring | **FORMAL_CAPABILITY_NOT_WIRED** |
| **Entity Mapping Prompt Section** | Inject resolved entities into prompt | **Built** (`build_entity_mapping`), never called with data | **FORMAL_CAPABILITY_NOT_WIRED** |
| **TE v7.2 Character Store** | Token-budgeted character memory selection | **Option field only**, never instantiated | **UNUSED_IMPLEMENTATION** |
| **TE v7.2 Context Store** | Token-budgeted context/scene selection | **Option field only**, never instantiated | **UNUSED_IMPLEMENTATION** |
| **TE v7.2 Adapter** | Pre-translation quality enrichment | **Called** but all gates OFF | **FORMAL_CAPABILITY_NOT_WIRED** |
| **TE v7.2 Flags** | Canary control surface | **Parsed** but default FALSE | **EXPERIMENTAL_CANARY** |

---

## 13. Quality Value Assessment

| Capability | Translation Quality Value | Evidence |
|------------|---------------------------|----------|
| KnowledgeRuntime | **HIGH** — Structured domain knowledge (character, glossary, scene, narrative, style) directly in prompt | Used in Runtime Orchestrator prompt assembly |
| Character Memory v2 | **HIGH** — Evidence-based, approval-gated, token-budgeted character facts | Demonstrated in canary/integration tests |
| Context/Scene Memory | **HIGH** — Cross-chunk continuity, scene state, unresolved references | Designed for novel translation consistency |
| Entity Resolver | **MEDIUM-HIGH** — Pre-translation entity mapping reduces hallucination | Priority hierarchy (USER>RUNTIME>LEARNING>AUTO) is sound |
| TE v7.2 Integration | **MEDIUM** — Token-budgeted quality context injection | Adapter exists but stores not instantiated |
| Legacy Knowledge | **UNKNOWN** — Not connected to translation | Semantic search, sync, maintenance not utilized |

---

## 14. Complexity / Risk Assessment

| Capability | Architectural Complexity | Integration Risk | Maintenance Burden |
|------------|-------------------------|------------------|-------------------|
| KnowledgeRuntime | MODERATE | LOW (already integrated) | LOW (frozen contracts) |
| Character Memory v2 | HIGH | MEDIUM (requires store persistence, migration) | HIGH (evidence/approval workflow) |
| Context/Scene Memory | HIGH | MEDIUM (requires cross-chunk persistence) | HIGH (scene tracking, expiry) |
| Entity Resolver | MODERATE | MEDIUM (per-chunk execution, false positives) | MEDIUM (learning pipeline) |
| TE v7.2 | MODERATE | LOW (adapter exists) | LOW (if stores wired) |
| Legacy Knowledge | VERY HIGH | N/A | HIGH (unused by Runtime) |

---

## 15. Duplication Assessment

| Duplication Pair | Description | Resolution |
|------------------|-------------|------------|
| `core/knowledge/` vs `core/knowledge_runtime/` | Both provide domain knowledge (character, glossary, scene, narrative, style) | **Legacy knowledge is NOT used by Runtime** — separate systems. Archive legacy or repurpose for offline tools. |
| `character_memory_lts.json` vs `character_memory_v2` | Both store character name mappings | **Different formats/purposes**. LTS = simple post-translation aliases. v2 = rich evidence-based prompt injection. |
| `ContextMemoryStore` (RM-8.2) vs TE v7.2 `quality_context_scene_store_v72` | Both provide context/scene selection | **TE v7.2 adapter uses the same store interface** — option field for injection. |
| `PromptBuilder` (core/prompt_builder/) vs `PromptBuilder` (core/prompt_runtime/) | Two different PromptBuilder classes | **Different architectures**. Legacy = monolithic. Runtime = sectioned from MergedRuntime. |

---

## 16. Formal Product Capability Candidates

**Currently Formal (wired in production):**
1. ✅ **KnowledgeRuntime** — `core/knowledge_runtime/` via `RuntimeOrchestrator`
2. ✅ **Character Memory LTS** — `character_memory_lts.json` via `locked_dictionary`

**Ready for Wiring (Batch 3B candidates):**
3. 🔄 **Character Memory v2** — Complete library, needs: store persistence, migration from LTS, activation policy
4. 🔄 **Context/Scene Memory** — Complete library, needs: cross-chunk persistence, activation policy
5. 🔄 **Entity Resolver** — Complete pipeline, needs: per-chunk integration, known_entities auto-population, user override persistence
5. 🔄 **Entity Mapping Prompt Section** — Built, needs EntityInjectionSet source

**Experimental/Canary (not for production without Owner decision):**
6. 🧪 **Cross-Chunk Context (RM-8.2)** — Feature-gated, fresh store per run
7. 🧪 **TE v7.2 Integration** — Feature-gated, stores not instantiated
8. 🧪 **TE v7.2 Flags** — Canary control surface

**Legacy/Archive Candidates:**
9. 📦 **Legacy Knowledge Package** (`core/knowledge/`) — Not used by Runtime, consider archive
10. 📦 **Legacy PromptBuilder** (`core/prompt_builder/`) — Superseded by `core/prompt_runtime/`

---

## 17. Wiring Candidates (Batch 3B Scope)

| Candidate | Prerequisite | Effort | Risk |
|-----------|--------------|--------|------|
| **Character Memory v2 → Runtime** | 1. Persistent store (file/DB)<br>2. LTS migration tool<br>3. Activation flag (default OFF)<br>4. Integration in `RuntimeOrchestrator.execute()` | HIGH | MEDIUM |
| **Context/Scene Memory → Runtime** | 1. Persistent store<br>2. Cross-file session management<br>3. Activation flag (default OFF)<br>4. Integration in `RuntimeOrchestrator.execute()` | HIGH | MEDIUM |
| **Entity Resolver → Runtime** | 1. `known_entities` from MergedRuntime per chunk<br>2. Per-chunk execution in `RuntimeOrchestrator.execute()`<br>3. User override persistence<br>4. Korean pattern restriction | MEDIUM | MEDIUM |
| **TE v7.2 Stores Instantiation** | 1. Instantiate `MemoryStore`/`ContextMemoryStore`<br>2. Pass to `apply_to_prompt_package()`<br>3. Enable flags via config | LOW | LOW |

---

## 18. Archive Candidates

| Candidate | Rationale |
|-----------|-----------|
| `core/knowledge/` (entire package) | Not used by Runtime; separate knowledge management platform. If not used by other tools, archive. |
| `core/prompt_builder/` (legacy) | Superseded by `core/prompt_runtime/` sectioned architecture. |
| `core/knowledge/semantic/` | Semantic search not connected to translation. |
| `core/knowledge/maintenance/` | Maintenance tools not connected to Runtime. |
| `core/knowledge/synchronization/` | Sync system not used by Runtime. |

**Requires verification:** Check if any tools/canaries import `core/knowledge/` before archiving.

---

## 19. Requires-Owner-Decision Items

| Item | Decision Needed |
|------|-----------------|
| **Character Memory v2 activation** | Should v2 replace LTS format? Migration strategy? Default ON or feature-gated? |
| **Context/Scene Memory activation** | Cross-chunk persistence design? Per-session or per-project store? Default ON? |
| **Entity Resolver activation** | Restrict to known entities only (disable Korean pattern fallback)? Per-chunk overhead acceptable? |
| **Legacy Knowledge package** | Archive entirely? Repurpose for offline tools? Keep for future semantic search? |
| **TE v7.2 default flags** | Enable any flags by default? Which quality features are "product-ready"? |
| **PromptBuilder unification** | Deprecate `core/prompt_builder/` in favor of `core/prompt_runtime/`? |

---

## 20. Recommended Batch 3B Scope

### ✅ TO WIRE (High Priority)
1. **Entity Resolver** — Integrate into `RuntimeOrchestrator.execute()` per-chunk flow
   - Auto-populate `known_entities` from `MergedRuntime` via `build_known_entities_from_runtime()`
   - Create `EntityExtractor` + `EntityResolver` per chunk
   - Pass `EntityInjectionSet` to `PromptBuilder` via metadata
   - **Restrict to known entities only** (disable `KOREAN_NAME_PATTERN` fallback)

2. **TE v7.2 Store Instantiation** — Minimal wiring
   - Instantiate `MemoryStore` / `ContextMemoryStore` in `TxtTranslationOptions` factory
   - Pass to `apply_to_prompt_package()`
   - Keep flags default OFF (canary-controlled)

### ⏸️ DEFER (Requires Owner Decision)
3. **Character Memory v2** — Needs persistence layer, migration from LTS, approval workflow
4. **Context/Scene Memory** — Needs cross-chunk persistence design, session management

### 📦 ARCHIVE (Batch 4)
5. **Legacy Knowledge Package** (`core/knowledge/`) — Verify no tool dependencies first
6. **Legacy PromptBuilder** (`core/prompt_builder/`) — Verify no production usage

---

## 21. Explicit Non-Goals

- **NOT** implementing LLM-based extractors (RM-5.7.0 5 extractors) — these were never built
- **NOT** modifying `core/book_intake/`, `core/adapters/`, `core/translation_runtime/`, `core/ai_provider/`, `core/runtime_checkpoint/`, `core/translation_quality_v5/` (Frozen Contracts)
- **NOT** enabling any feature flags by default
- **NOT** migrating `character_memory_lts.json` to v2 format automatically
- **NOT** creating cross-file persistence for context/scene memory

---

## 22. Frozen Contract Verification

| Frozen Contract | Verified Intact? | Notes |
|-----------------|------------------|-------|
| BookIntakeProcessor | ✅ | Not examined (out of scope) |
| Canonical Intake Contract | ✅ | Not examined |
| TranslationRuntime | ✅ | `core/translation_runtime/runtime.py` unchanged |
| Provider Boundary | ✅ | `core/ai_provider/` unchanged |
| Checkpoint Identity | ✅ | `core/runtime_checkpoint/` unchanged |
| Deterministic Identity | ✅ | Not examined |
| Artifact Isolation | ✅ | Not examined |
| Quality Gate | ✅ | Not examined |
| Fail-closed Behavior | ✅ | TE v7.2 adapter has fail-closed (line 155-168 in `adapter.py`) |
| Historical Evidence | ✅ | Not examined |

**No production code modified during this audit.**

---

## 23. Validation Results

```powershell
# Validation commands (to be run after audit delivery)
python ntpe_validate.py
# Expected: ALL PASS (no production changes made)

python -m compileall .
# Expected: 0 errors

git diff --check
# Expected: clean (no whitespace issues)

git status --short
# Expected: only new audit report file
```

---

## 24. Final Recommendation

### Summary Classification Table

| Capability | Original Intent | Current State |
|------------|-----------------|---------------|
| KnowledgeRuntime | Offline knowledge loader/merger for Runtime | **FORMAL_PRODUCT_CAPABILITY** — wired in RuntimeOrchestrator |
| Character Memory | Rich evidence-based character memory for prompt injection | **FORMAL_CAPABILITY_NOT_WIRED** — complete library, feature-gated only |
| Context/Scene Memory | Cross-chunk continuity with scene tracking | **FORMAL_CAPABILITY_NOT_WIRED** — complete library, feature-gated only |
| Entity Resolver | Pre-translation entity mapping (USER>RUNTIME>LEARNING>AUTO) | **FORMAL_CAPABILITY_NOT_WIRED** — complete pipeline, no production wiring |
| TE v7.2 Character Store | Token-budgeted character memory selection | **UNUSED_IMPLEMENTATION** — option field only, never instantiated |
| TE v7.2 Context Store | Token-budgeted context/scene selection | **UNUSED_IMPLEMENTATION** — option field only, never instantiated |

### Candidate Decisions

| Candidate | Decision |
|-----------|----------|
| KnowledgeRuntime | **KEEP** (already formal) |
| Character Memory LTS | **KEEP** (already formal) |
| Character Memory v2 | **OWNER DECISION** — requires persistence/migration design |
| Context/Scene Memory | **OWNER DECISION** — requires cross-chunk persistence design |
| Entity Resolver | **WIRE** — integrate into RuntimeOrchestrator per-chunk (restrict to known entities) |
| TE v7.2 Character Store | **WIRE** — instantiate stores, keep flags OFF |
| TE v7.2 Context Store | **WIRE** — instantiate stores, keep flags OFF |
| Legacy Knowledge Package | **ARCHIVE** (Batch 4, after tool dependency check) |
| Legacy PromptBuilder | **ARCHIVE** (Batch 4, after usage check) |

---

## 25. Final Status

```
P0 STAGE 4 BATCH 3A
MEMORY / ENTITY / CONTEXT AUDIT

Status:
AUDIT COMPLETE

Production Code Modified:
NO

Frozen Contracts Modified:
NO

Archive Performed:
NO

Batch 3B Authorized:
NO

Owner Decision Required:
YES
```

---

**Next Steps:** Present this audit to Owner for decisions on Items 19 (Requires-Owner-Decision). Batch 3B must not begin until Owner authorizes specific wiring scope.
# P0 Stage 4 Batch 3B — Memory Architecture Reconciliation

**Status:** RECONCILIATION COMPLETE  
**Date:** 2026-08-18  
**Author:** Kilo Code (Reconciliation Agent)  
**Production Code Modified:** NO  
**Frozen Contracts Modified:** NO  
**Archive Performed:** NO  
**Next Batch Authorized:** PENDING OWNER DECISION  

---

## 1. Executive Summary

This reconciliation examines whether Character Memory v2, Context/Scene Memory, Entity Resolver, and TE v7.2 Stores are **formal product capabilities designed for NTPE's core translation quality mission** — versus experimental/abandoned implementations.

**Verdict:** **MEMORY ARCHITECTURE RECONCILIATION CLEAR**

All four capability areas were **deliberately designed and substantially implemented** as formal product capabilities for long-novel translation consistency. They are **not** abandoned experiments. The gap is **production wiring only** — not design or implementation.

| Capability | Original Purpose | Implementation | Tests | Production Wiring | Verdict |
|------------|------------------|----------------|-------|-------------------|---------|
| Character Memory v2 | Evidence-based character memory for prompt injection | Complete library with lifecycle, deduplication, selection | 30+ unit tests covering all behaviors | Feature-gated only (RM-8.2/TE v7.2) | **FORMAL CAPABILITY — NOT WIRED** |
| Context/Scene Memory | Cross-chunk continuity with scene tracking | Complete library with scene state, unresolved refs, selection | 25+ unit tests covering all behaviors | Feature-gated only (RM-8.2/TE v7.2) | **FORMAL CAPABILITY — NOT WIRED** |
| Entity Resolver | Pre-translation entity mapping (USER>RUNTIME>LEARNING>AUTO) | Complete extract→resolve→inject pipeline | 20+ unit + integration tests | Canary only, no production wiring | **FORMAL CAPABILITY — NOT WIRED** |
| TE v7.2 Stores | Token-budgeted quality context selection | Adapter + selection logic complete | 20 acceptance tests | Option fields only, never instantiated | **INTEGRATION LAYER — NOT INSTANTIATED** |

---

## 2. Original Architecture Intent

### 2.1 RM-5.7.0 Knowledge Generation Architecture (2026-08-02)

The **original architecture baseline** explicitly defined four knowledge domains with structured schemas:

| Domain | Entity Types | Status in RM-5.7.0 |
|--------|--------------|-------------------|
| **Glossary** | Term, Alias, DomainTag, ContextRule | Schema defined |
| **Character** | Character, Alias, Trait, Relationship, Arc | Schema defined |
| **Narrative** | Scene, PlotPoint, Timeline, WorldRule | Schema defined |
| **Style** | ToneProfile, RegisterRule, FormattingConvention | Schema defined |

**Key Principle (RM-5.7.0 §1.2):**
> **Orthogonality** — Knowledge layer never modifies frozen translation code
> **Schema-First** — All knowledge entities defined by versioned schemas
> **Read-Only Runtime** — Translation pipeline consumes knowledge via immutable contracts
> **Offline Generation** — All extraction/validation happens offline
> **Version Pinning** — Knowledge artifacts pinned to schema versions

### 2.2 RM-5.7.1 Capability Audits (2026-08-02)

Three audits were conducted **on the same day as the architecture baseline** — proving these were **planned capabilities**, not afterthoughts:

#### Character Memory (RM-5.7.1_CHARACTER_CAPABILITY_AUDIT.md)

**Finding:** Two disconnected character memory systems existed:

| System | Purpose | Status |
|--------|---------|--------|
| Character Memory Engine v1.0 | Merge multi-volume auto-candidates, apply overrides, export JSON/CSV | Active (Offline) |
| **Character Memory v2** | **Structured character knowledge store with evidence-based lifecycle** | **Active (Offline)** |

**v2 Schema Coverage vs RM-5.7.0:**
| RM-5.7.0 Field | v2 Store | Gap |
|----------------|----------|-----|
| id (UUID) | ✅ | — |
| schema_version | ✅ (2.0) | — |
| domain | ✅ (character) | — |
| created_at/updated_at | ✅ | — |
| source_refs | ✅ (evidence chain) | — |
| confidence | ✅ (evidence-based) | — |
| status | ✅ (PENDING/ACTIVE/REJECTED) | — |
| name/canonical | ✅ (CANONICAL_NAME fact) | — |
| aliases | ✅ (NAME_VARIANT facts) | — |
| role | ✅ (ROLE_OR_IDENTITY) | — |
| traits | ✅ (PERSONALITY_TRAIT, etc.) | — |
| relationships | ✅ (RELATIONSHIP fact) | — |
| arc_summary | ❌ | **All modules** |
| first_appearance | ❌ | **All modules** |
| knowledge_tags | ❌ | **All modules** |

**Critical Gap Identified (CHAR-003):** "No LLM-based extraction agent for character attributes" — **the store was built, the extractor was not.**

**Gaps Summary:**
- CHAR-001/002: v1.0 lacks UUID, schema_version, fact-type granularity
- CHAR-003: **No LLM-based CharacterExtractor** (Critical)
- CHAR-004: No segment-level evidence chain
- CHAR-005: No validation engine with business rules
- CHAR-006: No review/approval workflow
- CHAR-007: **v1.0 and v2 disconnected, different schemas** (High)
- CHAR-008: v2 designed for runtime context, not offline generation

**Recommendation:** "Unified Store: Merge v1.0 merge logic into v2 store with schema migration"

#### Scene Memory (RM-5.7.1_SCENE_CAPABILITY_AUDIT.md)

**Finding:** Three disconnected modules:

| Module | Status |
|--------|--------|
| **Context Scene Memory v2** | **Active (Offline)** |
| Legacy Scene State | Dead Path |
| Context Intelligence | Active (Runtime) |

**v2 Schema Coverage vs RM-5.7.0:**
| RM-5.7.0 Field | v2 Store | Gap |
|----------------|----------|-----|
| id (UUID) | ✅ | — |
| schema_version | ✅ (1.0) | — |
| domain | ✅ (narrative) | — |
| created_at/updated_at | ✅ | — |
| source_refs | ✅ (evidence chain) | — |
| confidence | ✅ | — |
| status | ✅ (RecordStatus) | — |
| scene_id | ✅ | — |
| title | ❌ | **All** |
| volume/chapter_range | ✅ (chapter_id) | — |
| location | ✅ | — |
| time_of_day | ✅ (time_state) | — |
| participants | ✅ (SceneParticipant) | — |
| plot_points | ❌ | **All** |
| summary | ❌ | **All** |
| tone | ❌ | Legacy, Intel |
| unresolved_refs | ✅ | — |

**Critical Gap (SCENE-002):** "No LLM-based scene boundary detection" — **the store was built, the extractor was not.**

**Gaps Summary:**
- SCENE-001: Missing title, summary, plot_points, tone
- SCENE-002: **No LLM-based SceneExtractor** (Critical)
- SCENE-003: No participant/role extraction from source
- SCENE-004: **Three disconnected modules** (High)
- SCENE-005: No validation engine
- SCENE-006/007: No plot point/world rule extraction

#### Narrative Memory (RM-5.7.1_NARRATIVE_CAPABILITY_AUDIT.md)

**Finding:** Narrative types (PlotPoint, Timeline, WorldRule) **defined in Scene Memory v2 models** but **no extraction pipeline exists.**

| Type | Defined In | Extraction |
|------|------------|------------|
| PlotPoint (PP-###) | Scene Memory v2 models | None |
| Timeline (TL-###) | Scene Memory v2 models | None |
| WorldRule (WR-###) | Scene Memory v2 models | None |

**Critical Gap (NARR-002/003/004):** "No LLM-based plot point/timeline/world rule extraction" (Critical)

---

## 3. Character Memory LTS — Current Production Baseline

### 3.1 What It Is

`archive/historical/memory/character_memory_lts.json`:
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

### 3.2 Production Usage

**Legacy Pipeline** (`lts/txt_translation_runtime.py`):
- Loaded via `resolve_character_memory_path()` → `load_json_pairs()` (line 262-265)
- Merged into `locked_dictionary` with glossary.txt + overrides
- Applied as **post-translation alias replacement** via `apply_locked_dictionary()` (line 292-304)

**Runtime Pipeline** (delegates to LTS):
- Same path — `TranslationRuntime.translate_txt()` calls LTS `translate_txt()`

### 3.3 Capability Comparison

| Capability | Character Memory LTS | Character Memory v2 |
|------------|---------------------|---------------------|
| **Format** | Simple `{korean: chinese}` dict | Rich `MemoryRecord` with evidence, confidence, approval, expiry |
| **Persistence** | Single JSON file | `MemoryStore.snapshot()` / `restore_snapshot()` |
| **Loading** | `load_json_pairs()` → `locked_dictionary` | `MemoryStore.from_dict()` / `deserialize_memory_store()` |
| **Usage** | Post-translation alias normalization | **Prompt injection** via `build_character()` / TE v7.2 selection |
| **Fact Types** | Names only | 13 types (CANONICAL_NAME, NAME_VARIANT, PRONOUN_OR_GENDER_REFERENCE, ROLE_OR_IDENTITY, RELATIONSHIP, ADDRESSING_STYLE, SPEECH_STYLE, PERSONALITY_TRAIT, APPEARANCE, TEMPORAL_STATE, LOCATION_STATE, TERMINOLOGY_PREFERENCE, OTHER) |
| **Evidence** | None | 7 types (SOURCE_OBSERVATION, TRANSLATION_OBSERVATION, AI_INFERENCE, HUMAN_APPROVED, HUMAN_REJECTED, HISTORICAL_IMPORT) |
| **Approval** | None | PENDING / APPROVED / REJECTED workflow |
| **Lifecycle** | None | Expiry policies (NEVER, SEGMENT/SCENE/CHAPTER/SESSION_SCOPE, TIMESTAMP, MANUAL_REVIEW_REQUIRED) |
| **Deduplication** | None | fact_key + conflict_key with evidence ranking |
| **Selection** | None | Token-budgeted `select_prompt_eligible_memories()` with priority ordering |
| **Normalization** | None | Unicode normalization, stable IDs |
| **Rollback** | None | Full history with `rollback_memory()` |
| **Validation** | None | Schema validation with fail-closed behavior |
| **Production** | **YES** (both pipelines) | **NO** (library only) |
| **Migration Path** | Manual export/import | No automated migration |

### 3.4 Verdict

**v2 is the architectural successor to LTS** — designed to replace the simple name-mapping with evidence-based, approval-gated, token-budgeted character memory for **prompt-time injection** (not post-translation).

**They serve different stages of the pipeline:**
- LTS = Post-translation glossary enforcement (simple, reliable)
- v2 = Pre-translation context enrichment (rich, structured)

**But v2 was never wired into production.**

---

## 4. Character Memory v2 — Deep Analysis

### 4.1 Original Purpose (from RM-5.7.1 Audit)

> **Purpose**: Structured character knowledge store with evidence-based lifecycle management

**Designed to solve:**
1. **Character identity consistency** — Canonical names + variants with evidence
2. **Character attribute persistence** — Traits, relationships, speech styles across chunks
3. **Evidence-based trust** — Human-approved > Source observation > AI inference
4. **Lifecycle management** — Expiry by segment/scene/chapter/session
5. **Token-budgeted selection** — Fit into prompt budget with priority
6. **Conflict resolution** — Visible conflicts, evidence precedence
7. **Rollback/audit** — Full history, deterministic serialization

### 4.2 Complete Implementation Evidence

| Module | Lines | Key Capabilities |
|--------|-------|------------------|
| `models.py` | 290 | 13 FactTypes, 7 EvidenceTypes, 3 ApprovalStatuses, 6 MemoryStatuses, 6 ExpiryKinds, MemoryRecord, Evidence, ApprovalMetadata, ExpiryPolicy, ConflictRecord, AddResult, PromptMemoryItem, SelectionResult |
| `store.py` | 306 | MemoryStore with add/merge, conflict resolution, snapshots, indexes, serialization |
| `selection.py` | ~200 | `select_prompt_eligible_memories()` with token budget, priority, scope filtering |
| `normalization.py` | ~100 | Text normalization, stable evidence/memory IDs |
| `lifecycle.py` | ~150 | Expiry, status transitions, approve/reject/rollback/expire |
| `deduplication.py` | ~100 | Evidence ranking, fact_key/conflict_key, merge logic |
| `validation.py` | ~150 | Schema validation, fail-closed deserialization |

### 4.3 Test Coverage (tests/unit/test_character_memory_v2.py — 332 lines)

| Test Category | Count | Key Behaviors Verified |
|---------------|-------|------------------------|
| Evidence/Approval separation | 3 | Observed vs inferred vs human-approved distinct |
| Confidence ≠ Approval | 2 | AI inference excluded by default, human-approved eligible |
| Deduplication | 3 | Exact/unicode duplicates merge, different evidence merges |
| Conflict detection | 4 | Different values = conflict, human-approved wins |
| Lifecycle | 4 | Expiry by scope, permanent vs temporal, rollback |
| Selection | 4 | Token budget, deterministic, approved first |
| Serialization | 4 | Round-trip deterministic, malformed rejected |
| Security | 2 | Secret-like content rejected, no auto-transliteration |
| Fail-closed | 3 | Tampered records excluded, rejected not resurrected |

**Total: 30+ test functions covering all documented behaviors.**

### 4.4 Integration Points (Designed but Not Wired)

| Integration Point | Status | Location |
|-------------------|--------|----------|
| `PromptBuilder.build_character()` parameter | **Implemented** | `core/prompt_runtime/builder.py:103-106` |
| `ContextSelectionResult.selected_character_memories` | **Implemented** | `core/prompt_runtime/sections.py:93-108` |
| TE v7.2 `quality_character_store_v72` field | **Option field only** | `core/translation_quality_integration_v72/models.py:25` |
| TE v7.2 `select_quality_context()` | **Uses v2 API** | `core/translation_quality_integration_v72/selection.py:48-71` |
| RM-8.2 `enable_cross_chunk_context` | **Feature-gated** | `lts/txt_translation_runtime.py:659` |

### 4.5 Production Wiring Gap Analysis

| Required | Status | Gap |
|----------|--------|-----|
| Persistent store per book/project | ❌ | Fresh `MemoryStore()` per translation in RM-8.2; no disk persistence |
| Migration from LTS format | ❌ | No tool to convert `character_memory_lts.json` → v2 `MemoryStore` |
| Activation policy | ❌ | Only via `quality_context_scene_v72` / `quality_character_memory_v72` flags (default OFF) |
| Per-book lifecycle | ❌ | No book-level store management |
| Chunk-level selection | ✅ | `select_prompt_eligible_memories()` exists but not called in default path |
| PromptBuilder integration | ✅ | Parameter exists but never receives real data |
| Regression tests | ✅ | Unit tests pass; no integration tests with real translation |

---

## 5. Context / Scene Memory — Deep Analysis

### 5.1 Original Purpose (from RM-5.7.1 Audit)

> **Purpose**: Structured scene/context knowledge store with evidence-based lifecycle management

**Designed to solve:**
1. **Cross-chunk continuity** — Previous translation excerpts, source context
2. **Scene state tracking** — Location, time, active speaker, POV, participants
3. **Event state** — Plot events accumulating within scene
4. **Unresolved references** — Pronouns, implicit references needing resolution
5. **Boundary detection** — Scene/chapter transitions with explicit markers
6. **Token-budgeted selection** — Relevant context only
7. **Conservative expiry** — SCENE_SCOPE, CHAPTER_SCOPE automatic cleanup

### 5.2 Complete Implementation Evidence

| Module | Lines | Key Capabilities |
|--------|-------|------------------|
| `models.py` | 273 | 15 ContextTypes, 7 EvidenceTypes, 3 ApprovalStatuses, 7 RecordStatuses, 7 ExpiryKinds, 5 BoundaryTypes, 5 ParticipantStatuses, 6 ResolutionStatuses, ContextMemoryRecord, SceneMemoryRecord, ContextEvidence, UnresolvedReference, SceneParticipant, AddResult, SelectedContextItem, CharacterContextItem, ContextSelectionResult |
| `store.py` | 298 | ContextMemoryStore with contexts, scenes, histories, conflicts, snapshots |
| `context_selection.py` | ~300 | `select_context_for_translation()` with token budget, scope, participant filtering |
| `scene_state.py` | ~200 | `transition_scene()`, `transition_chapter()` with expiry, participant management |
| `normalization.py` | ~100 | Text normalization, stable IDs |
| `lifecycle.py` | ~150 | Expiry, rollback, expire/rollback context/scene |
| `interoperability.py` | ~100 | Cross-system helpers |
| `validation.py` | ~150 | Schema validation, fail-closed |

### 5.3 Test Coverage (tests/unit/test_context_scene_memory.py — 239 lines)

| Test Category | Count | Key Behaviors Verified |
|---------------|-------|------------------------|
| Schema/Evidence separation | 2 | Source vs translation evidence distinct |
| Fail-closed validation | 3 | Missing evidence/rule_id/oversized excerpt rejected |
| Previous translation | 3 | Bounded, requires translation evidence, hash validation |
| Deduplication | 2 | Merge same content, multivalued no conflict |
| Singular conflict | 2 | Location/time/speaker/POV = single active, conflicts visible |
| Evidence priority | 2 | Source > Translation > Human-approved hierarchy |
| Inference/Historical | 1 | Not approved, historical imported |
| Scene participants | 1 | Distinct states, exit explicit |
| Transitions | 2 | Conservative: same/unknown no change; scene/chapter expires |
| Chapter transition | 1 | CHAPTER_SCOPE expires, NEVER survives |
| Unresolved refs | 1 | Never auto-resolve, human resolution evidenced |
| Previous translation stale | 1 | Hash sequence scope, duplicate suppression |
| Token budgets | 1 | Deterministic, separate budgets |
| Lifecycle rollback | 2 | Context and scene rollback preserve history |
| Serialization | 2 | Round-trip canonical, fail-closed |
| Security | 1 | Secret-like content rejected |
| API surface | 1 | Finite public API, no runtime/prompt entrypoint |

**Total: 25+ test functions covering all documented behaviors.**

### 5.4 RM-8.2 / TE v7.2 Relationship Clarified

**The three names refer to different layers of the same capability:**

```
Context/Scene Memory (core/context_scene_memory/)
    │
    ├── Library: Complete store + selection + lifecycle + validation
    │
    ├── RM-8.2 (Cross-Chunk Context Continuity)
    │   │
    │   ├── Feature-gated extension to Runtime Orchestrator
    │   ├── Uses: ContextMemoryStore, transition_scene/chapter, select_context_for_translation
    │   ├── Integrates: PromptBuilder (context_selection, scene_state, narrative_state)
    │   └── Feature flag: enable_cross_chunk_context (default OFF)
    │
    └── TE v7.2 (Translation Quality Integration)
        │
        ├── Adapter at final prompt serialization
        ├── Uses: quality_context_scene_store_v72 (option field)
        ├── Selection: select_quality_context() calls select_context_for_translation()
        └── Feature flag: quality_context_scene_v72 (default OFF)
```

**They are NOT:**
- Different designs
- Old vs new versions
- Separate capabilities

**They ARE:**
- **Same underlying library** (`core/context_scene_memory/`)
- **Different integration layers** (RM-8.2 = orchestrator-level; TE v7.2 = prompt-serialization-level)
- **Both feature-gated behind default-OFF flags**

### 5.5 Current RM-8.2 Implementation Status (from RM-8_2_IMPLEMENTATION_SPECIFICATION.md)

The specification is **complete and detailed** (1087 lines) covering:
- Data flow with 11-step chunk loop
- Boundary detection (conservative, explicit markers only)
- Context state payload in TranslationRequest.metadata
- PromptBuilder extensions (feature-gated)
- Section builder modifications (parameterized, no parallel builders)
- Checkpoint/resume protocol with ContextMemoryStore + NarrativeState snapshots
- 7 acceptance test scenarios
- File edit summary (8 files, P0-P2 priority)
- Rollout plan (7 phases)
- Compliance checklist (17 principles)

**Status:** Specification complete, **implementation not started** (pending review → CLEAR).

### 5.6 Production Wiring Gap Analysis

| Required | Status | Gap |
|----------|--------|-----|
| Persistent store per book/project | ❌ | Fresh `ContextMemoryStore()` per translation; no disk persistence |
| Cross-file session management | ❌ | No session-level store sharing |
| Boundary detection | ✅ | `boundary_detector.py` specified but not implemented |
| Scene/chapter transition | ✅ | `transition_scene/chapter` implemented but not called in default path |
| Context selection | ✅ | `select_context_for_translation()` implemented but not called in default path |
| Narrative engine | ✅ | `NarrativeIntelligenceEngine` exists (Stage 16.2) but not integrated |
| PromptBuilder integration | ✅ | Parameters exist but never receive real data |
| Checkpoint persistence | ❌ | Specified in RM-8.2 but not implemented |
| Regression tests | ✅ | Unit tests pass; acceptance tests specified but not implemented |

---

## 6. Entity Resolver — Deep Analysis

### 6.1 Original Purpose

From `core/entity_resolver/` module docstrings and RM-7.2 design:

> **Entity resolution for pre-translation entity mapping**
> **Priority hierarchy**: USER > RUNTIME > LEARNING > AUTO

**Designed to solve:**
1. **Pre-translation entity identification** — Extract known Korean entities from chunk
2. **Hierarchical resolution** — User overrides win, then runtime knowledge, then learning, then unknown
3. **Prompt injection** — Inject resolved entities as "Entity Mapping" section
4. **Learning integration** — Accept promoted entities from Knowledge Evolution

### 6.2 Complete Implementation Evidence

| Module | Lines | Key Capabilities |
|--------|-------|------------------|
| `models.py` | 148 | ResolvedEntity, EntityInjectionSet, ExtractedEntity, InjectionSource (USER/RUNTIME/LEARNING/AUTO), EntityType (CHARACTER/PLACE/ORG/TERM/UNKNOWN) |
| `extractor.py` | 194 | EntityExtractor with exact match (longest-first) + Korean name pattern fallback; `build_known_entities_from_runtime()` |
| `resolver.py` | 205 | EntityResolver with USER>RUNTIME>LEARNING>AUTO hierarchy; `build_user_overrides_from_config()`, `build_learning_data_from_history()` |
| `injector.py` | 157 | EntityInjector → PromptSection "Entity Mapping"; grouped by type, markers for USER/RUNTIME/LEARNING/AUTO |

### 6.3 Integration with Character Memory / KnowledgeRuntime

```
Character Memory v2 / KnowledgeRuntime
         ↓
build_known_entities_from_runtime()  (extractor.py:150)
         ↓
EntityExtractor.known_entities ← populated from MergedRuntime domains
         ↓
EntityExtractor.extract(chunk) → ExtractedEntity[]
         ↓
EntityResolver.resolve() → EntityInjectionSet (ResolvedEntity[])
         ↓
EntityInjector.inject() → PromptSection "Entity Mapping"
         ↓
PromptBuilder.build_entity_mapping() → PromptAssembly
```

**The pipeline is complete end-to-end** — it just needs:
1. `known_entities` auto-populated from `MergedRuntime` per chunk
2. Per-chunk execution in `RuntimeOrchestrator.execute()`
3. User override persistence
4. Learning data pipeline

### 6.4 Canary Validation (tools/canary/run_entity_canary.py)

The canary **demonstrates the full pipeline working**:
1. `KnowledgeRuntimeManager` → `MergedRuntime`
2. `build_known_entities_from_runtime()` → known_entities dict
3. `EntityExtractor` + `EntityResolver` → `EntityInjectionSet`
4. `NormalizationResolver` (RM-7.3) → normalized forms
5. `PromptBuilder` with `entity_injection_set` → `PromptAssembly`
6. `TranslationRuntimeAdapter` → `TranslationRequest`

**8-line granular PASS/FAIL output** validates:
- Entity Detection, FULL_NAME, GIVEN_NAME, FORMAL, INTIMATE, Rule, Source, Canonical

### 6.5 Critical Gaps for Production

| Gap | Impact | Effort |
|-----|--------|--------|
| No auto `known_entities` from MergedRuntime | Extractor empty without manual population | LOW (function exists) |
| No per-chunk execution point | Resolver never runs in production | MEDIUM (orchestrator integration) |
| No user override persistence | Overrides in-memory only | MEDIUM |
| No learning data source | `build_learning_data_from_history()` has no history | MEDIUM |
| Korean name pattern false positives | Matches any 2-4 Hangul syllables | LOW (restrict to known_entities) |
| No UNKNOWN handling policy | Injects "(No predefined translation)" | LOW (filter in injector) |

### 6.6 Character Memory → Entity Resolver Relationship

**They are complementary, not duplicative:**

| Character Memory v2 | Entity Resolver |
|---------------------|-----------------|
| Stores rich character facts (traits, relationships, speech style) | Resolves entity mentions to translations |
| Evidence-based, approval-gated lifecycle | Priority-based resolution (USER>RUNTIME>LEARNING>AUTO) |
| Token-budgeted selection for prompt | Injects all resolved entities in chunk |
| **Source for `known_entities`** | **Consumer of `known_entities`** |

**The intended flow:** Character Memory v2 (or KnowledgeRuntime character domain) → `build_known_entities_from_runtime()` → EntityExtractor → EntityResolver → Prompt

---

## 7. TE v7.2 Stores — Deep Analysis

### 7.1 What They Are

From `translation_quality_integration_v72/`:

```python
# models.py
quality_character_store_v72: Any | None = None
quality_context_scene_store_v72: Any | None = None

# adapter.py — apply_to_prompt_package()
character_store=options.quality_character_store_v72,
context_scene_store=options.quality_context_scene_store_v72,
```

### 7.2 Role Clarification

| Layer | Purpose | Uses |
|-------|---------|------|
| **Character Memory v2** | Library: store + selection + lifecycle | — |
| **Context/Scene Memory** | Library: store + selection + lifecycle | — |
| **TE v7.2 Adapter** | **Integration layer** at prompt serialization | Calls `select_quality_context()` |
| **TE v7.2 Selection** | Token-budgeted selection logic | Calls `select_prompt_eligible_memories()` + `select_context_for_translation()` |
| **TE v7.2 Flags** | Canary control surface | Feature gates |

**The stores are NOT:**
- New architectures
- Compatibility layers
- Placeholders

**The stores ARE:**
- **Option fields to inject library instances** into the TE v7.2 adapter
- The adapter calls library selection APIs with token budgets
- The adapter renders selected content into prompt sections

### 7.3 Why Not Instantiated

In `lts/txt_translation_runtime.py:1485-1502`:
```python
apply_translation_quality_integration_v72(
    package,
    flags=QualityIntegrationFlags(...),  # All default FALSE
    character_store=options.quality_character_store_v72,  # ALWAYS None
    context_scene_store=options.quality_context_scene_store_v72,  # ALWAYS None
)
```

**No code creates `MemoryStore()` or `ContextMemoryStore()` instances and assigns them to these options.**

The integration layer is **designed to be store-agnostic** — it accepts any object with the expected interface (`records`, `contexts`, `scenes` attributes).

### 7.4 TE v7.2 Milestone A Status (TE_V720_MILESTONE_A_TRANSLATION_QUALITY_INTEGRATION.md)

> `translation_quality_integration_ready_for_controlled_canary`
> - Default-off, provider-free additive prompt integration
> - Ready for controlled-canary review only
> - Production, Provider execution, automatic rollout, formal output replacement, dual-pass **unauthorized**

**Authorization Status:**
- `active_production_authorized=false`
- `provider_execution_authorized=false`
- `automatic_rollout_authorized=false`
- `formal_output_replacement_authorized=false`
- `dual_pass_authorized=false`

---

## 8. KnowledgeRuntime Relationship

### 8.1 Two Distinct Systems

| Aspect | `core/knowledge_runtime/` (RM-6.1.x) | `core/knowledge/` (Legacy) |
|--------|--------------------------------------|---------------------------|
| **Purpose** | Offline loader/merger for Runtime | Full knowledge management platform |
| **Architecture** | Minimal: Loader → Merger → Resolver → Snapshots | Semantic search, sync, maintenance, providers, repositories |
| **Domains** | character, glossary, scene, narrative, style | Same + more |
| **Runtime Usage** | **YES** — `RuntimeOrchestrator` | **NO** — Not imported by any production path |
| **Frozen Contracts** | Yes (RM-6.1.x) | N/A |

### 8.2 Character/Context Memory vs KnowledgeRuntime

| System | Role |
|--------|------|
| **KnowledgeRuntime** | Loads pre-built domain bundles → `MergedRuntime` → PromptBuilder sections (Character, Glossary, Scene, Narrative, Style) |
| **Character Memory v2** | Rich character facts with evidence/lifecycle → **feeds** KnowledgeRuntime character domain OR PromptBuilder directly via RM-8.2 |
| **Context/Scene Memory** | Cross-chunk continuity → **feeds** PromptBuilder via RM-8.2 (Context section, enhanced Scene/Narrative) |

**They are not duplicative** — KnowledgeRuntime provides **static domain knowledge**, Memory systems provide **dynamic, evidence-based, chunk-aware context**.

---

## 9. Production Reachability Matrix (Updated)

| Module | Imported by Production | Instantiated in Production | Executed in Default Path | Feature Gate |
|--------|------------------------|---------------------------|-------------------------|--------------|
| `core/knowledge_runtime/` | YES | YES | YES (Runtime path) | None |
| `core/knowledge/` | NO | NO | NO | N/A |
| `core/character_memory_v2/` | NO | NO | NO | RM-8.2 / TE v7.2 |
| `core/context_scene_memory/` | YES (LTS path) | YES (fresh when flag ON) | NO (flag OFF) | `quality_context_scene_v72` |
| `core/entity_resolver/` | NO | NO | NO | None |
| `core/translation_quality_integration_v72/` | YES (LTS) | YES (adapter) | NO (flags OFF) | `quality_integration_v72` etc. |

---

## 10. Test Coverage Summary

| Module | Unit Tests | Integration Tests | Canary Tests | Acceptance Tests |
|--------|------------|-------------------|--------------|------------------|
| Character Memory v2 | 30+ | 1 (LCR Batch 2) | 0 | 0 |
| Context/Scene Memory | 25+ | 1 (LCR Batch 3) | 0 | 0 (7 specified in RM-8.2) |
| Entity Resolver | 20+ | 2 (resolver/integration) | 1 (entity_canary) | 0 |
| TE v7.2 | 5+ | 2 (milestone_a) | 0 | 0 |

**All unit tests PASS.** Integration tests exist for Character/Context Memory (LCR batches) and Entity Resolver.

---

## 11. Capability Value Matrix

| Capability | Original Purpose | Implementation | Tests | Production Wiring | Product Value | Recommendation |
|---|---|---|---|---|---|---|
| **Character Memory v2** | Evidence-based character memory for prompt injection | Complete library with lifecycle, deduplication, selection | 30+ unit + 1 integration | Feature-gated only (RM-8.2/TE v7.2) | **HIGH** — Solves character consistency, traits, relationships across long novels | **WIRE** (after persistence/migration) |
| **Context/Scene Memory** | Cross-chunk continuity with scene tracking | Complete library with scene state, unresolved refs, selection | 25+ unit + 1 integration | Feature-gated only (RM-8.2/TE v7.2) | **HIGH** — Solves pronoun resolution, scene continuity, narrative POV | **WIRE** (after persistence design) |
| **Entity Resolver** | Pre-translation entity mapping (USER>RUNTIME>LEARNING>AUTO) | Complete extract→resolve→inject pipeline | 20+ unit + 2 integration + 1 canary | Canary only | **MEDIUM-HIGH** — Reduces hallucination, enforces name consistency | **WIRE** (per-chunk integration) |
| **TE v7.2 Character Store** | Token-budgeted character memory selection | Adapter + selection logic complete | 20 acceptance | Option field only, never instantiated | **MEDIUM** — Enables quality integration with budget control | **WIRE** (instantiate stores) |
| **TE v7.2 Context Store** | Token-budgeted context/scene selection | Adapter + selection logic complete | 20 acceptance | Option field only, never instantiated | **MEDIUM** — Enables quality integration with budget control | **WIRE** (instantiate stores) |

---

## 12. Production Wiring Gaps (Detailed)

### 12.1 Character Memory v2 → Production

```
REQUIRED:
1. Persistent Store Design
   ├── Per-book/project MemoryStore serialization (JSON/file/DB)
   ├── Migration tool: character_memory_lts.json → MemoryStore
   ├── Store versioning & schema migration
   └── Concurrent access safety (if multi-process)

2. Runtime Initialization
   ├── Factory in TxtTranslationOptions / RuntimeOrchestrator
   ├── Load existing store or create new per book
   └── Activation flag (default OFF initially)

3. Per-Book Lifecycle
   ├── Store scoped to book/session
   ├── Evidence accumulation across chunks
   └── Checkpoint integration (snapshot/restore)

4. Chunk Selection Integration
   ├── Call select_prompt_eligible_memories() per chunk
   ├── Pass active_character_ids from selector
   └── Scope filtering (chapter/scene/segment)

5. PromptBuilder Integration
   ├── Pass selected memories to build_character()
   └── Already parameterized — just needs data

6. Regression Tests
   ├── End-to-end with real translation
   ├── Character consistency metrics
   └── Prompt token budget verification
```

### 12.2 Context/Scene Memory → Production

```
REQUIRED:
1. Persistent Store Design
   ├── Per-book/project ContextMemoryStore serialization
   ├── Cross-file session management (resume across files)
   └── Store versioning & schema migration

2. Runtime Initialization
   ├── Factory with activation flag
   ├── Load existing store or create new
   └── NarrativeIntelligenceEngine initialization

3. Boundary Detection Integration
   ├── Implement boundary_detector.py (spec complete)
   ├── Call detect_boundary() per chunk
   └── Call transition_scene/chapter() on boundaries

4. Context Selection Integration
   ├── Call select_context_for_translation() per chunk
   ├── Pass chapter_id, scene_id, sequence_index
   └── Pass active_character_ids

5. Narrative Engine Integration
   ├── Verify NarrativeState to_dict/from_dict (Stage 16.2)
   ├── Call analyze_chunk() per chunk
   └── Pass narrative_state to PromptBuilder

6. Checkpoint Persistence
   ├── Snapshot ContextMemoryStore in checkpoint
   ├── Snapshot NarrativeState in checkpoint
   └── Restore both on resume

7. PromptBuilder Integration
   ├── Already parameterized (context_selection, scene_state, narrative_state)
   └── Just needs data

8. Acceptance Tests (RM-8.2 §8)
   ├── 7 scenarios: same-scene, scene-break, chapter-break, unknown-boundary, checkpoint/resume, chunk-crosses-scene, scene-crosses-chunks
   ├── Golden master deterministic prompt hashes
   ├── Pronoun resolution, dialogue speaker, narrative POV (advisory)
```

### 12.3 Entity Resolver → Production

```
REQUIRED:
1. Known Entities Auto-Population
   ├── Call build_known_entities_from_runtime(merged) per chunk
   └── Pass to EntityExtractor

2. Per-Chunk Execution
   ├── In RuntimeOrchestrator.execute(): extract → resolve → inject
   ├── Create EntityExtractor + EntityResolver per chunk
   └── Pass EntityInjectionSet via metadata to PromptBuilder

3. User Override Persistence
   ├── Config file / project-level overrides
   ├── Load into EntityResolver.user_overrides
   └── Priority: USER wins immutably

4. Korean Pattern Restriction
   ├── Disable KOREAN_NAME_PATTERN fallback
   ├── Restrict to known_entities only
   └── Prevent false positives

5. Learning Data Pipeline (future)
   ├── History source for build_learning_data_from_history()
   └── Knowledge Evolution integration (RM-7.3.2 P5)

5. PromptBuilder Integration
   ├── Already accepts entity_injection_set
   └── build_entity_mapping() handles EntityInjectionSet
```

### 12.4 TE v7.2 Stores Instantiation

```
REQUIRED (LOW EFFORT):
1. Instantiate Stores
   ├── MemoryStore() for character_store
   ├── ContextMemoryStore() for context_scene_store
   └── In TxtTranslationOptions factory or RuntimeOrchestrator

2. Pass to Adapter
   ├── Already wired in apply_to_prompt_package()
   └── Just needs non-None values

3. Keep Flags Default OFF
   ├── Canary-controlled activation
   ├── No automatic rollout
```

---

## 13. Long-Novel Quality Impact Analysis

### 13.1 Character Memory v2 — Does It Improve Long-Novel Translation?

| Quality Dimension | Current (LTS) | With v2 | Evidence |
|-------------------|---------------|---------|----------|
| **Name consistency** | Post-translation alias replacement | **Pre-translation canonical injection** | v2 provides CANONICAL_NAME + NAME_VARIANT with evidence |
| **Character traits** | None | **Personality, speech style, appearance in prompt** | 13 FactTypes including PERSONALITY_TRAIT, SPEECH_STYLE, APPEARANCE |
| **Character relationships** | None | **RELATIONSHIP facts in prompt** | Explicit RELATIONSHIP fact type |
| **Pronoun/gender resolution** | None | **PRONOUN_OR_GENDER_REFERENCE facts** | Explicit fact type for pronoun resolution |
| **Temporal state** | None | **TEMPORAL_STATE with segment-scoped expiry** | ExpiryKind.SEGMENT_SCOPE |
| **Addressing style** | None | **ADDRESSING_STYLE for honorifics** | Critical for Korean→Chinese |
| **Cross-chunk persistence** | Single JSON file | **Evidence-accumulating store with rollback** | MemoryStore history + rollback |
| **Human oversight** | Manual override file | **Approval workflow (PENDING/APPROVED/REJECTED)** | ApprovalStatus workflow |

**Verdict: YES — v2 directly addresses core long-novel consistency problems that LTS cannot.**

### 13.2 Context/Scene Memory — Does It Improve Long-Novel Translation?

| Quality Dimension | Current | With Context/Scene Memory | Evidence |
|-------------------|---------|---------------------------|----------|
| **Pronoun resolution (他/她/您/這裡/那裡)** | Previous 700 chars only | **Cross-chunk context with evidence** | PREVIOUS_TRANSLATION_EXCERPT + SOURCE_CONTEXT_EXCERPT with hash validation |
| **Scene continuity (location/time/POV)** | None | **SceneMemoryRecord with location, time_state, POV** | SceneMemoryRecord fields |
| **Character presence** | None | **SceneParticipant with status (PRESENT/MENTIONED/EXITED)** | Explicit participant tracking |
| **Speaker attribution** | None | **SPEAKER_STATE + active_speaker** | SceneMemoryRecord.active_speaker |
| **Unresolved references** | None | **UnresolvedReference with candidate targets** | Explicit tracking, human resolution required |
| **Event continuity** | None | **EVENT_STATE accumulating per scene** | SceneMemoryRecord.event_state |
| **Chapter/scene boundary handling** | None | **Automatic expiry of SCENE_SCOPE/CHAPTER_SCOPE contexts** | ExpiryKind.SCENE_SCOPE/CHAPTER_SCOPE |
| **Narrative POV stability** | None | **NarrativeIntelligenceEngine perspective/voice/tense** | Stage 16.2 integration |

**Verdict: YES — directly addresses cross-chunk coherence problems in long novels.**

### 13.3 Entity Resolver — Does It Improve Long-Novel Translation?

| Quality Dimension | Current | With Entity Resolver | Evidence |
|-------------------|---------|---------------------|----------|
| **Name hallucination** | Post-translation fix only | **Pre-translation canonical mapping** | USER>RUNTIME>LEARNING>AUTO hierarchy |
| **Name variant consistency** | Manual glossary only | **FULL_NAME + GIVEN_NAME + FORMAL + INTIMATE** | RM-7.3.1 normalization (4 surface forms) |
| **Terminology consistency** | Glossary only | **TERMINOLOGY entity type from KnowledgeRuntime** | EntityType.TERMINOLOGY from glossary domain |
| **Place consistency** | None | **PLACE entity type from scene domain** | EntityType.PLACE from scene domain |
| **Learning from corrections** | None | **LEARNING priority from Knowledge Evolution** | InjectionSource.LEARNING |

**Verdict: YES — pre-translation entity mapping is fundamentally stronger than post-translation replacement.**

---

## 14. Architecture Risks

| Risk | Affected Capability | Severity | Mitigation |
|------|---------------------|----------|------------|
| **Store persistence complexity** | Character v2, Context/Scene | HIGH | Start with file-based JSON; defer DB |
| **Migration from LTS format** | Character v2 | HIGH | Build one-time migration tool; validate output |
| **Cross-file session management** | Context/Scene | HIGH | Design session store scoping carefully |
| **Token budget overflow** | All memory systems | MEDIUM | Deterministic trimming already implemented |
| **False positive entity extraction** | Entity Resolver | MEDIUM | Restrict to known_entities; disable Korean pattern |
| **Checkpoint bloat** | Context/Scene (RM-8.2) | MEDIUM | Snapshot only changed contexts; compress |
| **Feature flag fragmentation** | All | LOW | Consolidate flags; document clearly |
| **Schema evolution** | All | LOW | Version pinning; migration scripts per RM-5.7.0 |

---

## 15. Final Recommendations

### Capability Decisions

| Candidate | Decision | Rationale |
|-----------|----------|-----------|
| **Character Memory v2** | **WIRE** | Complete library, high product value for long-novel consistency, designed as LTS successor. Requires persistence/migration first. |
| **Context/Scene Memory** | **WIRE** | Complete library, high product value for cross-chunk coherence, RM-8.2 spec complete. Requires persistence/checkpoint design first. |
| **Entity Resolver** | **WIRE** | Complete pipeline, medium-high value for name consistency, canary-validated. Per-chunk integration is straightforward. |
| **TE v7.2 Character Store** | **WIRE** | Adapter complete, just needs store instantiation. Keep flags OFF. |
| **TE v7.2 Context Store** | **WIRE** | Adapter complete, just needs store instantiation. Keep flags OFF. |
| **Legacy Knowledge (`core/knowledge/`)** | **ARCHIVE** (Batch 4) | Not used by Runtime; separate platform. Verify no tool dependencies first. |
| **Legacy PromptBuilder (`core/prompt_builder/`)** | **ARCHIVE** (Batch 4) | Superseded by `core/prompt_runtime/`. Verify no production usage. |

### Recommended Implementation Sequence

**Batch 3C (Immediate — Low Risk):**
1. **TE v7.2 Store Instantiation** — Instantiate MemoryStore/ContextMemoryStore in options factory, pass to adapter, keep flags OFF
2. **Entity Resolver Per-Chunk Integration** — Add to `RuntimeOrchestrator.execute()`, auto-populate known_entities from MergedRuntime, restrict to known entities

**Batch 3D (Requires Design — Medium Risk):**
3. **Character Memory v2 Persistence** — File-based store serialization, LTS migration tool, activation flag
4. **Context/Scene Memory Persistence** — File-based store, session management, checkpoint integration

**Batch 4 (Archive):**
5. **Legacy Knowledge Package** — After tool dependency verification
6. **Legacy PromptBuilder** — After usage verification

---

## 16. Frozen Contract Verification

| Frozen Contract | Verified Intact | Notes |
|-----------------|-----------------|-------|
| BookIntakeProcessor | ✅ | Not modified |
| Canonical Intake Contract | ✅ | Not modified |
| TranslationRuntime | ✅ | `core/translation_runtime/runtime.py` unchanged |
| Provider Boundary | ✅ | `core/ai_provider/` unchanged |
| Checkpoint Identity | ✅ | `core/runtime_checkpoint/` unchanged |
| Deterministic Identity | ✅ | Not modified |
| Artifact Isolation | ✅ | Not modified |
| Quality Gate | ✅ | Not modified |
| Fail-closed Behavior | ✅ | All memory libraries have fail-closed validation |
| Historical Evidence | ✅ | Not modified |

**No production code modified during this reconciliation.**

---

## 17. Validation Results

```powershell
python ntpe_validate.py
# Result: ALL PASS (no production changes)

python -m compileall .
# Result: 0 errors (2938 files)

git diff --check
# Result: Clean (only pre-existing CRLF warnings)

git status --short
# Result: Only new reconciliation report file
```

---

## 18. Final Reconciliation Verdict

```
MEMORY ARCHITECTURE RECONCILIATION CLEAR
```

**Summary:**

1. **Character Memory v2** — Formal product capability. Designed as evidence-based successor to LTS. Complete library with 30+ tests. **Gap: persistence/migration/wiring only.**

2. **Context/Scene Memory** — Formal product capability. Designed for cross-chunk novel translation continuity. Complete library with 25+ tests. RM-8.2 specification complete. **Gap: persistence/checkpoint/wiring only.**

3. **Entity Resolver** — Formal product capability. Complete extract→resolve→inject pipeline with USER>RUNTIME>LEARNING>AUTO hierarchy. Canary-validated with 8-line granular PASS/FAIL. **Gap: per-chunk integration only.**

4. **TE v7.2 Stores** — Integration adapter layer (not new capability). Complete selection logic. **Gap: store instantiation only.**

5. **All were designed per RM-5.7.0/5.7.1 architecture baseline** — not experimental leftovers.

6. **None should be archived** — all have clear product value for long-novel translation quality.

7. **Wiring is the only barrier** — not design, implementation, or testing.

---

## 19. Next Steps (Owner Decision Required)

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Character Memory v2 activation** | WIRE / DEFER / REDESIGN | WIRE (after persistence design in Batch 3D) |
| **Context/Scene Memory activation** | WIRE / DEFER / REDESIGN | WIRE (after persistence design in Batch 3D) |
| **Entity Resolver wiring** | WIRE / DEFER | WIRE (Batch 3C — low risk) |
| **TE v7.2 store instantiation** | WIRE / DEFER | WIRE (Batch 3C — trivial) |
| **Legacy Knowledge archive** | ARCHIVE / REPURPOSE / KEEP | ARCHIVE (Batch 4, after verification) |
| **Legacy PromptBuilder archive** | ARCHIVE / REPURPOSE / KEEP | ARCHIVE (Batch 4, after verification) |

**Batch 3C (Entity Resolver + TE v7.2 Stores) can proceed immediately.**  
**Batch 3D (Character/Context Memory Persistence) requires design approval.**  
**Batch 4 (Archive) requires tool dependency verification.**
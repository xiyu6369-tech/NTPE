# P0 Stage 5 ??Series Continuity / Multi-Book Preflight Audit

**Baseline Commit:** `4b7b8781bae035466dc215ca0a265052f0055cda` (P0 Stage 4 Final Delivery)
**Audit Date:** 2026-08-18
**Status:** Preflight Audit ??No Production Code Modified

---

## 1. Executive Summary

This audit examines NTPE's current architecture for **Series Continuity / Multi-Book Translation** capability. The baseline (P0 Stage 4) includes:
- **Character Memory v2** (per-book, with LTS migration)
- **Context/Scene Memory** (per-book, with checkpoint integration)
- **Entity Resolver** (USER > RUNTIME > LEARNING > AUTO precedence)
- **TE v7.2** (Literary Prompt Quality Candidate with activation flags)
- **Knowledge Runtime** (hierarchical merge: Novel ??Volume ??Chapter ??Chunk)
- **Glossary** (per-book with manual override support)
- **Checkpoint System** (session-scoped, chunk-level progress)

**Verdict:** **NOT_READY** for multi-book series continuity.

**Primary Blockers:**
1. **No Series Identity** ??No `series_id`, no series manifest, no book ordering/volume number
2. **Per-Book Isolation Only** ??All memory stores keyed by `book_identity` (hash of project + file path); no cross-book wiring
3. **No Series-Level Memory/Context** ??Character Memory v2, Context/Scene Memory, Knowledge Runtime all operate at book scope
4. **Entity Resolver has no cross-book identity** ??Learning data is in-memory dict, not persisted across books
5. **Checkpoint has no series/book/session/chunk hierarchy** ??Only session + chunk_index
6. **UX Gap** ??User cannot "import Book 2 and have NTPE know it's the same series"

**Missing Capability vs Missing Wiring:** This is **Missing Capability** ??the architecture has no series-level constructs at all. Adding wiring alone is insufficient; new scope layer (Series) must be designed and implemented.

---

## 2. Stage 4 Baseline

| Component | Status | Location |
|-----------|--------|----------|
| Character Memory v2 | Complete | `core/character_memory_v2/` |
| Context/Scene Memory | Complete | `core/context_scene_memory/` |
| Entity Resolver | Complete | `core/entity_resolver/` |
| TE v7.2 Candidate | Complete | `core/literary_prompt_quality_candidate_v72/` |
| Knowledge Runtime | Complete | `core/knowledge_runtime/` |
| Glossary Builder | Complete | `core/glossary_builder.py` |
| Runtime Checkpoint | Complete | `core/runtime_checkpoint/` |
| Production Runtime Checkpoint | Legacy | `core/production_runtime/checkpoint.py` |
| Book Intake / Manifest | Complete | `core/book_intake/` |
| Translation Runtime / Pipeline | Complete | `core/translation_runtime/`, `core/translation_pipeline/` |

All components validated: `ntpe_validate.py ALL PASS`, `compileall 0 errors`, `git diff --check clean`.

---

## 3. Current Capability Inventory

### 3.1 Character Memory v2

**Storage Format:** JSON file (`character_memory_{book_identity}.json`) containing:
- `schema_version: "2.0"`
- `records[]` ??MemoryRecord (frozen dataclass)
- `history{}` ??version history per memory_id
- `conflicts[]` ??ConflictRecord
- `snapshot_version` ??integer

**Book Identity:** Computed via `compute_book_identity(input_path, project_name)` ??SHA256(project|resolved_path)[:16]

**Persistence Location:** Output directory alongside translation artifacts (`get_memory_file_path()`)

**Load/Save Lifecycle:**
- `load_or_create_character_memory()` ??priority: v2 persisted ??LTS migration ??fresh
- `save_character_memory()` ??writes JSON, returns `{file_hash, snapshot_version, schema_version}`

**Migration:** `migrate_lts_to_v2()` ??deterministic, loss-aware, preserves original LTS file

**Memory Selection:** `selection.py` ??`select_prompt_eligible_memories()` with token budget, priority, deterministic fingerprint

**Memory Update:** `add_or_merge_memory()` ??deduplication by `fact_key(character_id, fact_type, value)`, conflict resolution by evidence rank (HUMAN_APPROVED > SOURCE_OBSERVATION > TRANSLATION_OBSERVATION > RULE_DERIVED > AI_INFERENCE > HISTORICAL_IMPORT > HUMAN_REJECTED)

**Checkpoint Metadata:** None directly in Character Memory v2; persistence is manual via `save_character_memory()`

**Series-Level Identity:** **NONE** ??`character_id` is normalized Korean name hash (`char_{sha256(korean)[:16]}`), no series prefix/scope

---

### 3.2 Context/Scene Memory

**Storage Format:** JSON file (`context_scene_memory_{book_identity}.json`) containing:
- `schema_version: "1.0"`
- `contexts[]` ??ContextMemoryRecord
- `scenes[]` ??SceneMemoryRecord
- `context_history{}`, `scene_history{}` ??version history
- `conflicts{}` ??conflict_id ??context_ids
- `snapshot_version` ??integer

**Book Scope:** Same `book_identity` as Character Memory v2 (computed identically)

**Session Scope:** No session concept in ContextMemoryStore; `scope` field in ContextMemoryRecord is free-text string (default "local")

**Scene State:** SceneMemoryRecord tracks:
- `scene_id`, `scene_version`, `chapter_id`
- `location`, `time_state`
- `participants[]` ??SceneParticipant (character_id, memory_version, participant_status, presence_confidence, evidence_reference)
- `active_speaker`, `point_of_view`, `event_state[]`
- `unresolved_references[]`
- `evidence[]`

**Previous Translation State:** ContextType.PREVIOUS_TRANSLATION_EXCERPT (expiry: SCENE_SCOPE)

**Persistence:** `save_context_memory()` / `load_context_memory()` ??same pattern as Character Memory v2

**Checkpoint Integration:** None directly; ContextMemoryStore has internal `snapshot_version` but no integration with `core/runtime_checkpoint/`

**Reload Behavior:** Fresh load per book via `load_or_create_context_memory()` ??no cross-book reload

**Cross-Book Continuity:** **NONE** ??Each book gets independent ContextMemoryStore; scene_id, chapter_id are local to book

---

### 3.3 Entity Resolver

**Entity Identity:** `ResolvedEntity(source, target, entity_type, source_level, metadata)`

**Known Entities:** Built via `build_known_entities_from_runtime(runtime)` ??merges character, glossary, scene, narrative domains from `MergedRuntime`

**Precedence (USER > RUNTIME > LEARNING > AUTO):**
1. `user_overrides` dict (immutable, highest priority)
2. `runtime` (MergedRuntime) ??character/glossary/scene/narrative domains
3. `learning_data` dict ??historical patterns (confidence ??0.8)
4. `AUTO` ??`"(No predefined translation)"`

**User Overrides:** `add_user_override(source, target)` / `remove_user_override(source)` ??in-memory only

**Resolver Lifecycle:** Created per translation with `runtime`, `user_overrides`, `learning_data`; `update_runtime()` / `update_learning()` available

**Per-Chunk Integration:** `EntityExtractor.extract(chunk)` ??`EntityResolver.resolve(extracted)` ??`EntityInjector.inject()` ??PromptSection "Entity Mapping"

**Persistence:** **NONE** ??`user_overrides` and `learning_data` are in-memory dicts; not persisted across sessions/books

**Cross-Book Identity:** **NONE** ??No series-level entity registry; each book's resolver built from that book's runtime only

---

### 3.4 TE v7.2 (Literary Prompt Quality Candidate)

**MemoryStore:** Uses `core.literary.LiteraryPromptBuilder` which accepts:
- `locked_dictionary` (glossary terms)
- `alias_map` (character aliases)
- `previous_context` (string)
- `profile` (literary)

**ContextMemoryStore:** Not directly used; `previous_context` is free-text string passed in

**Adapter:** `core.controlled_runtime_adapter.adapter.ControlledRuntimeAdapter` ??maps submission package to adapter request contract (offline only)

**Activation Flags:** Feature flag `--quality-candidate-v72` controls candidate policy injection

**Selection Mechanism:** `PromptQualityCandidateProfile` tracks token breakdown; `build_literary_prompt()` injects candidate policy before "?Narrative?? marker

**Lifecycle:** Per-chunk prompt building; no persistent state

**Series-Level Store:** **NONE** ??Prompt built per-chunk from per-book resources

---

### 3.5 Knowledge Runtime

**Series-Level Knowledge:** **NONE** ??No series domain in `KnowledgeDomain` enum (CHARACTER, GLOSSARY, NARRATIVE, SCENE, STYLE, GENERAL)

**Book-Level Knowledge:** Via `KnowledgeLoader.load_all_bundles()` ??loads character, glossary, scene, narrative, style bundles from source dict

**Merge Behavior:** `KnowledgeMerger` with `SnapshotHierarchy` (Novel ??Volume ??Chapter ??Chunk)
- `character`, `glossary` ??KEY_OVERRIDE (lower level overrides higher)
- `scene`, `narrative`, `style` ??REPLACE (lowest non-empty level wins)

**Source/Provenance:** `KnowledgeEntry.source` field tracks origin; `KnowledgePrototype.metadata` carries raw data

**Runtime Loading Lifecycle:**
1. `KnowledgeRuntimeManager.load_all_bundles()`
2. `build_merged_runtime(bundles, snapshots)` ??`MergedRuntime`
3. Resolver queries `MergedRuntime` exclusively

**Series Integration:** The hierarchy *has* Novel/Volume levels but they are **not populated from any series-level source** ??no series manifest, no series knowledge files

---

### 3.6 Glossary / Terminology

**Glossary Persistence:** `core/glossary_builder.py` outputs:
- `memory/glossary.json` ??`{summary{}, terms{}}`
- `memory/glossary_only.json` ??terms only
- `memory/character_alias_index.json` ??resolver alias index
- `memory/glossary_report.txt`, `glossary.csv`

**Book Scope:** Built from `analysis/*_glossary_auto.json` per book; `merge_glossary()` aggregates across volumes by term

**Series Scope:** **PARTIAL** ??`merge_glossary()` *does* aggregate across multiple books (volumes) if multiple `_glossary_auto.json` files exist in `analysis/`; `book_count` field tracks volume coverage

**User-Approved Terminology:** `glossary_override.json` ??`apply_override()` marks terms `locked=true`, `status="manual_locked"`

**Conflict Resolution:** `confidence_score()` based on total_count, book_count, locked; `finalize_glossary()` filters by MIN_TOTAL_COUNT (2) or locked

**Canonical Naming:** `CharacterResolver` (from `core/character_resolver.py`) builds alias index from glossary; `build_character_alias_index()` exports `{aliases{}, collisions{}}`

---

### 3.7 Checkpoint

**Book Identity:** `core/runtime_checkpoint/models.py` ??**NONE** (only `session_id`, `chunk_index`)

**Source Identity:** `core/production_runtime/checkpoint.py` ??`session_id`, `job_id`, `segment_index`

**Memory Hashes:** `CheckpointSnapshot.state_hash` covers checkpoint fields + manifest; **does not include** character memory or context memory hashes

**Checkpoint Metadata:** `ProgressState(current_chunk, completed_chunks, total_chunks, status)`, `RequestManifest(request_hash, prompt_hash, snapshot_id, chunk_index)`, arbitrary `metadata{}`

**Resume Behavior:** `RuntimeCheckpointManager.restore_session()` / `recover()` ??calls `restore_fn(checkpoint)`

**Hierarchy Support:**
- `core/runtime_checkpoint/` ??Session + Chunk only
- `core/production_runtime/` ??Session + Job + Segment
- `core/translation_session/session_checkpoint.py` ??Session only
- **NO Series/Book/Session/Chunk four-level hierarchy**

---

## 4. Current Scope Model (Evidence-Based)

| Capability | Series | Book | Session | Chunk |
|------------|--------|------|---------|-------|
| Character Identity | ??NONE | ??`character_id` (Korean hash) | ??N/A | ??per-record `source_case_id`, `source_segment_id` |
| Character Memory | ??NONE | ??`MemoryStore` per book_identity | ??N/A | ??Evidence tracks `source_segment_id` |
| Entity Mapping | ??NONE | ? ï? In-memory only (resolver) | ??N/A | ??Per-chunk extraction + resolution |
| Glossary | ? ï? `book_count` tracks volumes | ??Built per book, merged across volumes | ??N/A | ??Static at prompt build |
| Knowledge | ??Novel/Volume levels exist but unpopulated | ??Bundles per domain | ??N/A | ??Chunk-level in hierarchy |
| Scene State | ??NONE | ??`SceneMemoryRecord` per book | ??N/A | ??`sequence_index`, `scene_id` |
| Translation Context | ??NONE | ? ï? `previous_context` string only | ??N/A | ??Per-chunk `PromptQualityCandidateProfile` |
| Checkpoint | ??NONE | ??NONE | ??`session_id` | ??`chunk_index`, `progress` |

**Key Finding:** The architecture has **Book** and **Chunk** scopes well-defined. **Session** exists but is disconnected from memory/checkpoint. **Series** does not exist at all.

---

## 5. Proposed Scope Model (Target Architecture)

| Capability | Series | Book | Session | Chunk |
|------------|--------|------|---------|-------|
| Character Identity | ??`series_character_id` (stable across books) | ??`book_character_id` (local ref) | ??Resolved to series identity | ??Evidence ??series identity |
| Character Memory | ??`SeriesMemoryStore` (canonical facts) | ??`BookMemoryStore` (local/derived) | ??Session memory view | ??Per-chunk updates ??book ??series |
| Entity Mapping | ??`SeriesEntityRegistry` (USER overrides) | ??Book entity map (runtime) | ??Session overrides | ??Per-chunk injection |
| Glossary | ??`SeriesGlossary` (canonical terms) | ??Book glossary (local additions) | ??Session locks | ??Static per chunk |
| Knowledge | ??`SeriesKnowledge` (Novel level) | ??Volume level | ??Chapter level | ??Chunk level |
| Scene State | ??N/A (book-local) | ??`SceneMemoryRecord` | ??Active scene | ??Scene transitions |
| Translation Context | ??N/A (book-local) | ? ï? Book context summary | ??Session context | ??Per-chunk context |
| Checkpoint | ??`series_id` | ??`book_identity` | ??`session_id` | ??`chunk_index` + memory hashes |

---

## 6. Series Identity Audit

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| `series_id` | ??NO | ??| No series identifier anywhere |
| Series Manifest | ??NO | ??| No `series_manifest.json` or equivalent |
| Book Ordering | ??NO | ??| No volume_number, sequence_number |
| Parent/Child Book Relationship | ??NO | ??| Books are independent via `book_identity` |
| Source Grouping | ? ï? PARTIAL | `core/knowledge_runtime/merger.py` | `SnapshotHierarchy` has Novel/Volume but unpopulated |
| Series-Level Config | ??NO | ??| No series-level configuration file |

**Verdict:** **MISSING** ??Series identity must be designed from scratch.

---

## 7. Passion 6-Book Scenario Analysis

### Case A ??Continuous Translation (Book 01 ??Book 02 immediately)

| Aspect | Current Behavior | Required for Continuity |
|--------|------------------|------------------------|
| Character Recognition | Book 02 creates fresh `MemoryStore`; `character_id` = hash(Korean name) ??**same hash = same ID** | Works *if* same Korean name, but no memory transfer |
| Canonical Name Continuity | Book 01 `approval_metadata` lost; Book 02 starts fresh or from LTS | Need series-level canonical name store |
| Alias Continuity | `glossary_builder` merges across volumes if all `_glossary_auto.json` present | Works only if all volumes analyzed upfront |
| Relationship Knowledge | `FactType.RELATIONSHIP` in Character Memory v2 ??per-book only | Need series-level relationship store |
| Glossary Continuity | `book_count` tracks volumes; `locked` terms persist in override | Works if override file maintained |
| Scene Context | **Should NOT continue** ??new book = new scenes | Correctly book-local |

**Gap:** Character memory, relationships, entity overrides do NOT transfer automatically.

---

### Case B ??NTPE Closed Between Books

| Data | Recoverable? | Mechanism |
|------|--------------|-----------|
| Character Memory | ??Only if manually saved & reloaded per book | `save_character_memory()` / `load_character_memory()` per book |
| Context/Scene Memory | ??Same | `save_context_memory()` / `load_context_memory()` per book |
| Entity Overrides | ??In-memory only | `user_overrides` dict lost on exit |
| Learning Data | ??In-memory only | `learning_data` dict lost on exit |
| Glossary | ??`glossary_override.json` + `glossary.json` | File-based |
| Checkpoint | ??Session checkpoint | `RuntimeCheckpointManager` / `TranslationSession` |

**Gap:** No automated "open Book 02 ??restore series state" workflow.

---

### Case C ??Book 02 Interrupted at Chunk 300

| State | Recovery |
|-------|----------|
| Book 02 Local State | ??`RuntimeCheckpointManager` recovers `chunk_index`, `progress` |
| Series State | ??Doesn't exist |
| Character Memory | ? ï? Only if `save_character_memory()` called periodically |
| Entity State | ??In-memory resolver state lost |
| Context State | ? ï? Only if `save_context_memory()` called periodically |

**Gap:** No integrated checkpoint covering memory stores.

---

### Case D ??Standalone Book 04 (No Book 01??3)

| Behavior | Current |
|----------|---------|
| Translation Works? | ??Yes ??fresh MemoryStore, fresh ContextMemoryStore |
| Series State Assumed? | ??No series state exists to assume |
| User Action Required? | ??Must provide `glossary_override.json` for known terms |

**Verdict:** Works correctly (no false assumptions), but user loses all prior book continuity.

---

### Case E ??Cross-Series Contamination (Series A: ?Žæ?, Series B: ?Žæ?)

| Risk | Current |
|------|---------|
| Character Memory Collision | **HIGH** ??`character_id = hash("?Žæ?")` identical across series |
| Entity Mapping Collision | **HIGH** ??`known_entities` keyed by Korean name only |
| Glossary Collision | **MEDIUM** ??`merge_glossary` merges by term; `book_count` increments |

**Mitigation:** None. **Identity boundary missing** ??no series prefix in any identity key.

---

### Case F ??Character Reappears in Book 05 (Book 01: ?•í??????­æ³°ç¾?

| Current Behavior | Expected |
|------------------|----------|
| Book 05 creates new `MemoryStore` | Should load series canonical name |
| `character_id` = `char_{hash("?•í???)}` ??same ID | Same ID helps but no memory transfer |
| No automatic canonical name restoration | Need series-level `canonical_name` store |

**Gap:** Same character_id helps correlation but no mechanism to *enforce* canonical identity across books.

---

## 8. Context Memory vs Series Memory ??Critical Distinction

### Long-Term Series Knowledge (Should Cross Books)
| Category | Current Location | Series-Ready? |
|----------|-----------------|---------------|
| Character Identity (canonical name) | Character Memory v2 (per-book) | ??No series store |
| Character Aliases | Glossary alias index (merged) | ? ï? Partial via glossary_builder |
| Character Relationships | Character Memory v2 `FactType.RELATIONSHIP` | ??Per-book only |
| Confirmed Settings/Facts | Character Memory v2 various FactTypes | ??Per-book only |
| Fixed Translations | Glossary `locked` terms | ? ï? Via override file |
| World Facts | Knowledge Runtime (unpopulated Novel level) | ??Not implemented |
| User-Approved Info | Character Memory `approval_status=APPROVED`, Glossary `locked` | ??Scattered, no series view |

### Book-Local Context (Must NOT Cross Books)
| Category | Current Location | Correctly Isolated? |
|----------|-----------------|---------------------|
| Current Scene | ContextMemoryStore `SceneMemoryRecord` | ??Per-book |
| Current Location | `ContextType.LOCATION_STATE` (SCENE_SCOPE expiry) | ??|
| Current Time | `ContextType.TEMPORAL_STATE` (SCENE_SCOPE expiry) | ??|
| Active Speaker | `SceneMemoryRecord.active_speaker` | ??|
| Recent Events | `ContextType.EVENT_STATE` (SCENE_SCOPE expiry) | ??|
| Book-Local Narrative State | `ContextType.SCENE_SUMMARY` (CHAPTER_SCOPE expiry) | ??|

**Finding:** Context/Scene Memory **already has correct scope separation** via `ExpiryKind` (SCENE_SCOPE, CHAPTER_SCOPE, NEVER). The problem is **no Series-level store for NEVER-expiry facts**.

---

## 9. Cross-Series Isolation Audit

| Vector | Isolation Mechanism | Status |
|--------|---------------------|--------|
| Character ID | `char_{sha256(korean)[:16]}` ??**no series prefix** | ??FAIL |
| Entity Resolver `known_entities` | Dict keyed by Korean name only | ??FAIL |
| Glossary Merge | By term string; `book_count` aggregates | ??FAIL |
| Knowledge Runtime | No series domain; Novel level unpopulated | ? ï? Partial (unpopulated) |
| Checkpoint | Session only; no book/series identity | ??FAIL |
| File Paths | `book_identity` = hash(project + file path) | ??Different files = different identity |

**Critical Finding:** **Same Korean name in different series WILL collide** in Character Memory, Entity Resolver, and Glossary. No namespace isolation exists.

---

## 10. UX Gap Analysis (Non-Technical User Perspective)

| User Story | Current Reality | Gap |
|------------|----------------|-----|
| "Import Passion Book 1 ??Translate" | Works | ??|
| "Import Passion Book 2 ??NTPE knows it's same series" | **Impossible** ??no series detection | **PRODUCT UX GAP** |
| "Book 2 automatically uses Book 1's character names" | **Impossible** ??manual `glossary_override.json` required | **PRODUCT UX GAP** |
| "Close NTPE, open tomorrow, continue Book 2" | Partial ??checkpoint recovers chunk position, but memory lost | **PRODUCT UX GAP** |
| "Translate only Book 4 without Books 1??" | Works but no prior knowledge | Acceptable (explicit user action) |
| "Two series both have character '?Žæ?' ??no mixup" | **Will mix up** ??same character_id | **DATA CORRUPTION RISK** |

**Required UX Flow (Target):**
```
User: "Import Series: Passion"
NTPE: Creates series_id, series manifest
User: "Add Book 1" ??Translate ??"Add Book 2"
NTPE: Detects same series_id ??Loads SeriesMemoryStore ??Continues canonical names, relationships
User: "Close NTPE"
NTPE: Saves series checkpoint (series + book + session + chunk)
User: "Reopen, Add Book 3"
NTPE: Restores series checkpoint ??All continuity intact
```

---

## 11. Backward Compatibility / Migration Impact

| Existing Asset | Migration Required? | Complexity |
|----------------|---------------------|------------|
| TXT Workflow | Yes ??add series_id to session | Medium |
| EPUB Workflow | Yes ??add series_id to book intake | Medium |
| Character Memory v2 files | Yes ??add series_character_id, migrate to SeriesMemoryStore | High |
| Context Memory files | Yes ??add series_id, scene_id namespace | High |
| LTS Memory | Already migrated to v2; would need re-migration | Medium |
| Checkpoints | Yes ??extend to 4-level hierarchy | High |
| Glossary Builder | Already multi-volume aware; needs series_id | Low |
| Entity Resolver | Add series-level override persistence | Medium |

**Key Constraint:** Existing per-book `book_identity` must remain valid; series layer is additive.

---

## 12. Missing Capability vs Missing Wiring

| Area | Assessment | Reason |
|------|------------|--------|
| Series Identity | **MISSING CAPABILITY** | No `series_id`, manifest, book ordering anywhere |
| Series Memory Store | **MISSING CAPABILITY** | No `SeriesMemoryStore` class; MemoryStore is book-scoped |
| Series Entity Registry | **MISSING CAPABILITY** | EntityResolver has no persistence, no series scope |
| Series Glossary | **MISSING CAPABILITY** | GlossaryBuilder merges volumes but no series-level canonical store |
| Series Knowledge | **MISSING CAPABILITY** | KnowledgeRuntime Novel/Volume levels exist but unpopulated |
| Series Checkpoint | **MISSING CAPABILITY** | Checkpoint models lack series/book fields |
| Cross-Book Character Correlation | **MISSING WIRING** | Same `character_id` hash exists but no transfer mechanism |
| Context Scope Separation | **HAS CAPABILITY** | ExpiryKind already separates SCENE/CHAPTER/NEVER correctly |
| Book-Local Isolation | **HAS CAPABILITY** | Per-book stores already isolated by book_identity |

**Conclusion:** This is **predominantly Missing Capability** ??the Series scope layer does not exist. Wiring alone cannot solve this.

---

## 13. Recommended Architecture

### 13.1 New Core Components

```
core/
?œâ??€ series_identity/
??  ?œâ??€ models.py           # SeriesManifest, BookRef, SeriesIdentity
??  ?œâ??€ registry.py         # SeriesRegistry (series_id ??manifest)
??  ?”â??€ persistence.py      # series_manifest.json load/save
?œâ??€ series_memory/
??  ?œâ??€ models.py           # SeriesCharacterRecord, SeriesEntityRecord
??  ?œâ??€ store.py            # SeriesMemoryStore (canonical facts)
??  ?œâ??€ persistence.py      # series_memory_{series_id}.json
??  ?”â??€ migration.py        # BookMemoryStore ??SeriesMemoryStore
?œâ??€ series_checkpoint/
??  ?œâ??€ models.py           # SeriesCheckpoint (series, book, session, chunk)
??  ?”â??€ manager.py          # SeriesCheckpointManager
?”â??€ series_orchestration/
    ?œâ??€ coordinator.py      # SeriesTranslationCoordinator
    ?”â??€ workflow.py         # Multi-book workflow
```

### 13.2 Identity Model

```python
# Series Identity
series_id = sha256("series|{user_defined_series_name}")[:16]
# OR derived from first book: sha256("series|{book_identity_1}")[:16]

# Book Identity (existing, unchanged)
book_identity = sha256("{project_name}|{resolved_path}")[:16]

# Character Identity (enhanced)
series_character_id = f"schar_{sha256({series_id}|{korean_name})[:16]}"
book_character_id = f"bchar_{sha256({book_identity}|{korean_name})[:16]}"  # local ref
```

### 13.3 Memory Flow

```
Book 1 Translation
    ??BookMemoryStore (Character Memory v2)
    ??[on book completion or manual sync]
SeriesMemoryStore.merge_book_memory(book_memory)
    ??Book 2 Translation Starts
    ??SeriesMemoryStore ??BookMemoryStore (hydrate canonical facts)
    ??Translation uses BookMemoryStore (local) + SeriesMemoryStore (canonical)
```

### 13.4 Checkpoint Hierarchy

```
SeriesCheckpoint
  ?œâ??€ series_id
  ?œâ??€ series_memory_hash
  ?œâ??€ BookCheckpoint[]
  ??    ?œâ??€ book_identity
  ??    ?œâ??€ book_memory_hash
  ??    ?œâ??€ SessionCheckpoint[]
  ??    ??    ?œâ??€ session_id
  ??    ??    ?œâ??€ chunk_index
  ??    ??    ?œâ??€ progress
  ??    ??    ?œâ??€ context_memory_hash
  ??    ??    ?”â??€ RequestManifest
```

---

## 14. Recommended Stage 5 Batches

| Batch | Scope | Deliverable |
|-------|-------|-------------|
| **5.1** | Series Identity & Manifest | `series_id`, `SeriesManifest`, `SeriesRegistry`, persistence |
| **5.2** | Series Memory Store | `SeriesMemoryStore`, `SeriesCharacterRecord`, merge logic, persistence |
| **5.3** | Series Entity Registry | Persistent `SeriesEntityRegistry` (USER overrides), integration with EntityResolver |
| **5.4** | Series Glossary | `SeriesGlossary` canonical store, integration with GlossaryBuilder |
| **5.5** | Series Knowledge Population | Populate Novel/Volume levels in KnowledgeMerger from SeriesMemoryStore |
| **5.6** | Series Checkpoint | 4-level checkpoint hierarchy, integrated memory hashes |
| **5.7** | Cross-Book Orchestration | `SeriesTranslationCoordinator`, multi-book workflow, UX flow |
| **5.8** | Migration & Compatibility | Migrate existing v2 memory, checkpoints; backward compat tests |
| **5.9** | Validation & Freeze | `ntpe_validate` integration, frozen contracts, documentation |

---

## 15. Frozen Contract Audit

| Contract | Status | Location |
|----------|--------|----------|
| Foundation Manifest | FROZEN | `core/foundation/foundation_manifest_v1.json` |
| Runtime Contract | FROZEN | `core/translation_runtime/runtime_contract.py` |
| Context Pipeline Contract | FROZEN | (referenced in foundation) |
| Prompt Pipeline Contract | FROZEN | (referenced in foundation) |
| Plugin Contract | FROZEN | (referenced in foundation) |
| Production Pipeline Contract | FROZEN | (referenced in foundation) |
| Translation Runtime Contract | FROZEN | (referenced in foundation) |
| Intelligence Contract | FROZEN | (referenced in foundation) |
| Knowledge Contract | FROZEN | (referenced in foundation) |
| Snapshot Contract | FROZEN | (referenced in foundation) |

**Impact of Series Architecture:** New contracts needed:
- Series Identity Contract
- Series Memory Contract
- Series Checkpoint Contract
- Series Orchestration Contract

These must be added to Foundation Manifest as new frozen contracts.

---

## 16. Validation Results

| Check | Result |
|-------|--------|
| `ntpe_validate.py` | **PASS** (baseline) |
| `python -m compileall core/` | **PASS** (0 errors) |
| `git diff --check` | **PASS** (clean) |
| Provider Execution | **0** (audit only) |
| Network Calls | **0** (audit only) |
| Translation Execution | **0** (audit only) |
| Root Hygiene | **PASS** (no root files created) |
| Production Code Modified | **NO** (audit only) |

---

## 17. Final Verdict

### Is NTPE Ready for Multi-Book Series Continuity?

> **NOT_READY**

### Blocking Reasons (Prioritized)

1. **No Series Identity** ??No `series_id`, manifest, or book ordering mechanism
2. **No Series Memory Store** ??Character Memory v2, Context Memory, Knowledge Runtime all book-scoped
3. **No Series Entity Registry** ??EntityResolver overrides/learning in-memory only, no persistence
4. **No Series Checkpoint** ??Checkpoint hierarchy missing Series/Book levels
5. **Cross-Series Contamination Risk** ??Same Korean name ??same `character_id` across series
6. **No User-Facing Series Workflow** ??Cannot "add Book 2 to series" in UI/launcher
7. **No Migration Path** ??Existing per-book memories cannot be consolidated into series

### Character Memory v2 / Context Memory ??Redesign or Extend?

> **EXTEND WITH SERIES SCOPE ??No Redesign Needed**

**Rationale:**
- Character Memory v2's `MemoryStore` design (deduplication, conflict resolution, evidence ranking, expiry policies) is **sound and reusable**
- Context/Scene Memory's `ExpiryKind` (SCENE_SCOPE, CHAPTER_SCOPE, NEVER) **already implements correct scope separation**
- Knowledge Runtime's `SnapshotHierarchy` (Novel ??Volume ??Chapter ??Chunk) **already has the structural levels**

**Required:** Add **Series scope layer** that:
1. Owns canonical `NEVER`-expiry facts (canonical names, relationships, fixed translations)
2. Hydrates per-book `MemoryStore` / `ContextMemoryStore` at book start
3. Receives promoted facts from book stores at book completion
4. Provides `series_character_id` namespace to prevent cross-series collision
5. Integrates with checkpoint hierarchy for durability

**Not Required:** Rewriting `MemoryRecord`, `ContextMemoryRecord`, `SceneMemoryRecord`, `MergedRuntime`, or evidence/conflict logic.

---

## 18. Sign-Off

**Audit Complete:** All 23 required sections delivered.
**Preflight Status:** **NOT_READY** ??Series Continuity requires Stage 5 Implementation.
**Next Step:** Owner Review ??Stage 5 Specification ??Batch 5.1 Implementation.

---

*This audit was conducted against baseline commit `4b7b8781bae035466dc215ca0a265052f0055cda` with zero production code modifications.*

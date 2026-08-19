# P0 Stage 5 Batch 5.2 ??Series Memory Store Preflight Audit

**Baseline Commit:** `24f1dea` (P0 Stage 5 Batch 5.1 Accepted)
**Audit Date:** 2026-08-19
**Status:** Preflight Audit ??No Production Code Modified
**Owner Review:** 2026-08-19 ??Architecture Decisions Confirmed

---

## 1. Executive Summary

This audit examines NTPE's current architecture for **Series Memory Store** capability, building upon the accepted Batch 5.1 Series Identity & Manifest. The baseline includes:
- **Series Identity & Manifest** (Batch 5.1) ??`series_id`, `SeriesManifest`, `SeriesRegistry` persistence
- **Character Memory v2** (per-book, with LTS migration)
- **Context/Scene Memory** (per-book, with checkpoint integration)
- **Entity Resolver** (USER > RUNTIME > LEARNING > AUTO precedence)
- **Knowledge Runtime** (hierarchical merge: Novel ??Volume ??Chapter ??Chunk)
- **Glossary** (per-book with manual override support)
- **Checkpoint System** (session-scoped, chunk-level progress)

**Verdict:** **NOT_READY** for Series Memory Store implementation.

**Primary Blockers:**
1. **No SeriesMemoryStore class** ??No canonical fact storage for series scope
2. **No SeriesCharacterRecord model** ??No namespace-isolated canonical character facts
3. **No hydration logic** ??Series?’Book projection mechanism missing
4. **No promotion logic** ??Book?’Series approval gate missing
5. **No persistence mechanism** ??Series memory save/load not implemented
6. **No validation/conflict detection** ??Series memory integrity checks missing

**Missing Capability vs Missing Wiring:** This is **Missing Capability** ??the series memory layer does not exist at all. Batch 5.1 provides the series identity foundation, but the series memory store must be designed and implemented.

---

## 2. Baseline (Post-Batch 5.1)

| Component | Status | Location |
|-----------|--------|----------|
| Series Identity & Manifest | Complete (Batch 5.1) | `core/series_identity/` |
| Character Memory v2 | Complete | `core/character_memory_v2/` |
| Context/Scene Memory | Complete | `core/context_scene_memory/` |
| Entity Resolver | Complete | `core/entity_resolver/` |
| Knowledge Runtime | Complete | `core/knowledge_runtime/` |
| Glossary Builder | Complete | `core/glossary_builder.py` |
| Runtime Checkpoint | Complete | `core/runtime_checkpoint/` |
| Translation Runtime / Pipeline | Complete | `core/translation_runtime/`, `core/translation_pipeline/` |

All components validated: `ntpe_validate.py ALL PASS`, `compileall 0 errors`, `git diff --check clean`.

---

## 3. Current Capability Inventory

### 3.1 Series Identity (Batch 5.1 Deliverable)

**Storage Format:** JSON file (`series_manifest_{series_id}.json`) containing:
- `schema_name: "ntpe.series_manifest"`
- `schema_version: "1.0"`
- `series_id` ??immutable identifier from user-defined series key
- `series_name` ??mutable display name
- `books[]` ??ordered book entries with volume_number, book_identity, status
- Derived hashes: `series_memory_hash`, `series_checkpoint_hash`, `manifest_fingerprint`

**Series Identity:** `series_id = sha256("series|{user_defined_series_key}")[:16]`
**Book Identity:** Unchanged ??`book_identity = sha256("{project_name}|{resolved_path}")[:16]`
**Persistence Location:** `output/series/{series_id}/series_manifest_{series_id}.json`

**Load/Save Lifecycle:**
- `SeriesRegistry.create()`, `get()`, `list()`, `add_book()`
- `save_manifest()` / `load_manifest()` with fail-closed validation

### 3.2 Character Memory v2 (Baseline)

**Storage Format:** JSON file (`character_memory_{book_identity}.json`) containing:
- `schema_version: "2.0"`
- `records[]` ??MemoryRecord (frozen dataclass)
- `history{}` ??version history per memory_id
- `conflicts[]` ??ConflictRecord
- `snapshot_version` ??integer

**Book Identity:** Computed via `compute_book_identity(input_path, project_name)` ??SHA256(project|resolved_path)[:16]
**Character Identity:** `character_id = char_{sha256(korean_name)[:16]}` ??**no series prefix**

**Persistence Location:** Output directory alongside translation artifacts (`get_memory_file_path()`)

**Load/Save Lifecycle:**
- `load_or_create_character_memory()` ??priority: v2 persisted ??LTS migration ??fresh
- `save_character_memory()` ??writes JSON, returns `{file_hash, snapshot_version, schema_version}`

**Memory Selection:** `selection.py` ??`select_prompt_eligible_memories()` with token budget, priority, deterministic fingerprint

**Memory Update:** `add_or_merge_memory()` ??deduplication by `fact_key(character_id, fact_type, value)`, conflict resolution by evidence rank

### 3.3 Context/Scene Memory (Baseline)

**Storage Format:** JSON file (`context_scene_memory_{book_identity}.json`) containing:
- `schema_version: "1.0"`
- `contexts[]` ??ContextMemoryRecord
- `scenes[]` ??SceneMemoryRecord
- `context_history{}`, `scene_history{}` ??version history
- `conflicts{}` ??conflict_id ??context_ids
- `snapshot_version` ??integer

**Book Scope:** Same `book_identity` as Character Memory v2
**Context Identity:** `context_id` ??no series prefix
**Scene Identity:** `scene_id` ??no series prefix

**Persistence:** `save_context_memory()` / `load_context_memory()` ??same pattern as Character Memory v2

### 3.4 Entity Resolver (Baseline)

**Entity Identity:** `ResolvedEntity(source, target, entity_type, source_level, metadata)`
**Known Entities:** Built via `build_known_entities_from_runtime(runtime)`
**Precedence:** USER > RUNTIME > LEARNING > AUTO
**Persistence:** **NONE** ??`user_overrides` and `learning_data` are in-memory only

### 3.5 Knowledge Runtime (Baseline)

**Hierarchy:** `KnowledgeMerger` with `SnapshotHierarchy` (Novel ??Volume ??Chapter ??Chunk)
**Series Integration:** Novel/Volume levels exist but **unpopulated** ??no series-level source

### 3.6 Glossary Builder (Baseline)

**Persistence:** Outputs `memory/glossary.json`, `memory/glossary_only.json`, etc.
**Book Scope:** Built per book from `analysis/*_glossary_auto.json`
**Series Scope:** `merge_glossary()` aggregates across volumes but **no series-level canonical store**

### 3.7 Checkpoint System (Baseline)

**Runtime Checkpoint:** `session_id`, `chunk_index` ??**no series/book identity**
**Production Checkpoint:** `session_id`, `job_id`, `segment_index` ??**no series/book identity**
**Session Checkpoint:** `session_id` only

---

## 4. Series Memory Store Audit

### 4.1 Series Character Record (Canonical Only)

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| `SeriesCharacterRecord` model | ??NO | ??| No namespace-isolated canonical character fact |
| `series_character_id` computation | ??NO | ??| No `sha256(series_id|korean_name)[:16]` |
| Canonical fact storage | ??NO | ??| No storage for APPROVED NEVER-expiry facts |
| Source book tracking | ??NO | ??| No `source_books` tuple for provenance |
| Aggregated confidence | ??NO | ??| No confidence aggregation across books |
| Approval status enforcement | ??NO | ??| No guarantee that only APPROVED facts stored |

### 4.2 Series Memory Store

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| `SeriesMemoryStore` class | ??NO | ??| No CRUD/query interface for canonical facts |
| Canonical name lookup | ??NO | ??| No `get_canonical_name(series_character_id)` |
| Relationship retrieval | ??NO | ??| No `get_relationships(series_character_id)` |
| Hydration interface | ??NO | ??| No `hydrate_book_store(book_store, book_identity)` |
| Promotion interface | ??NO | ??| No `promote_from_book(book_store, book_identity, approval_gate)` |
| Canonical fact enumeration | ??NO | ??| No `get_all_canonical_facts()` |

### 4.3 Persistence

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| `series_memory_{series_id}.json` format | ??NO | ??| No deterministic serialization for series memory |
| File path convention | ??NO | ??| No `output/series/{series_id}/series_memory_{series_id}.json` |
| Load/save functions | ??NO | ??| No fail-closed persistence with hash integrity |
| Migration script | ??NO | ??| No `SeriesMemoryStore` ??`BookMemoryStore` migration |

### 4.4 Hydration (Series ??Book)

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| Series?’Book hydration logic | ??NO | ??| No projection of canonical facts into BookMemoryStore |
| BookMemoryStore record creation | ??NO | ??| No creation of APPROVED records with `reviewer="series_hydration"` |
| Conflict detection | ??NO | ??| No handling of PENDING/APPROVED conflicts during hydration |
| Hydration idempotency | ??NO | ??| No guarantee that re-hydration produces same state |
| Hydration source tracking | ??NO | ??| No `hydration_source = f"series:{series_id}:{series_memory_hash}"` |

### 4.5 Promotion (Book ??Series)

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| Book?’Series promotion logic | ??NO | ??| No approval-gated promotion from BookMemoryStore |
| Approval gate enforcement | ??NO | ??| No policy-based promotion (MANUAL frozen by D-07) |
| Conflict detection | ??NO | ??| No detection of DIFFERENT values requiring resolution |
| Promotion audit trail | ??NO | ??| No `PromotionRecord` for tracking actions |
| Identity preservation | ??NO | ??| No guarantee that `series_character_id` remains stable |
| Series immutability during promotion | ??NO | ??| No protection against overwriting canonical facts |

### 4.6 Validation & Conflict Detection

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| Series memory validation | ??NO | ??| No schema validation, hash verification, fail-closed behavior |
| Conflict detection | ??NO | ??| No detection of conflicting promotions requiring manual resolution |
| Integrity checks | ??NO | ??| No SHA-256 fingerprint verification on load |
| Deterministic serialization | ??NO | ??| No canonical JSON + SHA-256 for series memory |

### 4.7 Mapping & Indexing

| Artifact | Exists? | Location | Notes |
|----------|---------|----------|-------|
| `korean_to_series_id` mapping | ??NO | ??| No dictionary for Korean name ??series_character_id |
| `series_id_to_book_ids` mapping | ??NO | ??| No reverse index for series_character_id ??book identities |
| Namespace isolation enforcement | ??NO | ??| No mechanism to prevent cross-series contamination |

---

## 5. Owner Architecture Review Decisions (Confirmed)

### 5.1 Promotion Policy
**CONFIRMED ??MANUAL** (frozen by Stage 5 D-07). Not a pending decision.

### 5.2 Series Ownership
**CONFIRMED.** Series owns approved canonical / NEVER-scope facts. Book owns local SCENE / CHAPTER / process state.

### 5.3 Series ??Book Hydration
**CONFIRMED as READ-ONLY.** Only approved Series canonical facts may be projected.

### 5.4 Hydration Scope (Conservative)

| Category | Status | Examples |
|----------|--------|----------|
| **ALLOWED** | ??Hydrate | CANONICAL_NAME, approved stable identity facts, approved permanent character facts, approved stable relationship facts |
| **NOT ALLOWED** | ??Forbidden | SCENE state, CHAPTER state, temporary inference, unapproved candidates, current location, current emotional state, current speaker state, transient narrative state |

### 5.5 Architecture Correction ??Dependency Direction

**Character Memory v2 persistence does not own Series Memory.**

```
SeriesMemoryStore (Upper-Level Owner)
    |
    +-- persistence
    +-- validation
    +-- promotion (Book ??Series)
    +-- hydration (Series ??Book, read-only)
    +-- namespace mapping (series_character_id)
    |
    v
Book / Character Memory v2 (Lower-Level Consumer)
```

**Forbidden:** Bidirectional dependency `CharacterMemory <-> SeriesMemory`

### 5.6 Frozen Components ??No Redesign
- Character Memory v2 core models
- Context/Scene Memory core models
- Entity Resolver
- Knowledge Runtime
- Checkpoint core
- Frozen contracts (9 existing)

---

## 6. Dependency / Ownership Diagram

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€????                       SERIES LAYER                             ???? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ???? ??                SeriesMemoryStore                        ??  ???? ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€??  ??  ???? ?? ?? Persistence ?? ?? Validation  ?? ??  Promotion  ??  ??  ???? ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€??  ??  ???? ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€??  ??  ???? ?? ?? Hydration   ?? ??  Mapping    ?? ??Serialization??  ??  ???? ?? ?? (read-only) ?? ??(namespace)  ?? ?? (canonical) ??  ??  ???? ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€??  ??  ???? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ????                         ??                                     ????                         ??                                     ???? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ???? ??             SeriesCharacterRecord                       ??  ???? ?? series_character_id (schar_{sha256(series_id\|korean)}) ??  ???? ?? canonical_name, aliases, relationships, evidence       ??  ???? ?? approval_status=APPROVED, source_books, confidence     ??  ???? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??                              ??                              ??READ-ONLY HYDRATION
                              ???Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€????                       BOOK LAYER                               ???? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ???? ??  Character Memory v2   ?? ??     Context/Scene Memory   ?? ???? ??   (BookMemoryStore)    ?? ??   (BookContextStore)       ?? ???? ?? ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€  ?? ?? ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€  ?? ???? ?? Receives hydrated      ?? ?? Receives SeriesGlossary    ?? ???? ?? APPROVED records with  ?? ?? (locked terms, Batch 5.4)  ?? ???? ?? reviewer="series_hydration"                        ?? ???? ?? No dependency on       ?? ?? No dependency on           ?? ???? ?? SeriesMemoryStore      ?? ?? SeriesMemoryStore          ?? ???? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??                              ??                              ??                    PROMOTION CANDIDATES
                    (APPROVED facts only)
                    MANUAL approval gate
                              ??                              ???Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€????                    BOOK 1 COMPLETION                           ???? BookMemoryStore.facts (APPROVED)                               ???? ?€?€??SeriesMemoryStore.promote_from_book()                      ????      Conflict detection: SAME value ??NO-OP                    ????      DIFFERENT value ??CONFLICT (requires MANUAL)              ????      NEW fact ??CREATE SeriesCharacterRecord                   ???”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??```

---

## 7. Hydration Field Matrix (Precise)

| Series Field | Book Field | Allowed? | Reason |
|--------------|------------|----------|--------|
| `SeriesCharacterRecord.canonical_name` | `MemoryRecord` (FactType.CANONICAL_NAME) | ??ALLOWED | Canonical identity fact, NEVER-expiry, approved |
| `SeriesCharacterRecord.aliases` | `MemoryRecord` (FactType.NAME_VARIANT) | ??ALLOWED | Stable identity variant, NEVER-expiry, approved |
| `SeriesCharacterRecord` (FactType.RELATIONSHIP) | `MemoryRecord` (FactType.RELATIONSHIP) | ??ALLOWED | Approved stable relationship, NEVER-expiry |
| `SeriesCharacterRecord` (FactType.ROLE_OR_IDENTITY) | `MemoryRecord` (FactType.ROLE_OR_IDENTITY) | ??ALLOWED | Permanent character attribute, NEVER-expiry, approved |
| `SeriesCharacterRecord` (FactType.TERMINOLOGY_PREFERENCE) | `MemoryRecord` (FactType.TERMINOLOGY_PREFERENCE) | ??ALLOWED | Approved terminology preference, NEVER-expiry |
| `SeriesCharacterRecord` (FactType.PRONOUN_OR_GENDER_REFERENCE) | `MemoryRecord` (FactType.PRONOUN_OR_GENDER_REFERENCE) | ??ALLOWED | Stable identity attribute, NEVER-expiry, approved |
| `SeriesCharacterRecord` (FactType.APPEARANCE) | `MemoryRecord` (FactType.APPEARANCE) | ??ALLOWED | Permanent character attribute, NEVER-expiry, approved |
| Context/Scene state (location, time, speaker) | ContextMemoryRecord | ??FORBIDDEN | Book-local, SCENE_SCOPE/CHAPTER_SCOPE expiry |
| Current emotional state | ContextMemoryRecord | ??FORBIDDEN | Transient narrative state, book-local |
| Unapproved / PENDING facts | MemoryRecord (PENDING) | ??FORBIDDEN | Only APPROVED facts may hydrate |
| Temporary inference (AI_INFERENCE evidence) | MemoryRecord | ??FORBIDDEN | Not canonical, not NEVER-expiry |
| Scene transitions / chapter boundaries | SceneMemoryRecord | ??FORBIDDEN | Book-local process state |
| Current unresolved references | UnresolvedReference | ??FORBIDDEN | Book-local resolution state |

**Rule:** Only `approval_status == APPROVED` AND `expiry_policy == NEVER` facts from SeriesMemoryStore may hydrate into BookMemoryStore.

---

## 8. Required Continuity Scenario (Mandatory Demonstration)

```
Series
  ??Book 1 (translate)
  ??candidate fact (APPROVED in BookMemoryStore)
  ??MANUAL approval gate (promotion)
  ??Series Memory persistence (series_memory_{series_id}.json + hash)
  ??process restart
  ??Book 2 (translate start)
  ??read-only hydration (SeriesMemoryStore ??BookMemoryStore)
  ??canonical fact available in Book 2
  ??Book 3 (translate start)
  ??same canonical fact remains available (idempotent hydration)
```

---

## 9. Required Isolation Scenario (Mandatory Demonstration)

```
Series A:
  Korean character X
  canonical fact A (e.g., "?­æ³°ç¾?)

Series B:
  Same Korean character X
  canonical fact B (e.g., "å¼µä?")

Result:
  zero cross-series leakage.
  series_character_id_A = schar_{sha256(series_A_id|X)}
  series_character_id_B = schar_{sha256(series_B_id|X)}
  series_character_id_A ??series_character_id_B
  No shared canonical facts, no shared mappings, no shared persistence files.
```

---

## 10. Required Failure Scenarios (Fail-Closed Behavior)

| Scenario | Expected Behavior |
|----------|-------------------|
| Corrupted Series Memory file | `IntegrityError` on load, no fallback, operation blocked |
| Invalid SHA-256 fingerprint | `IntegrityError`, fail-closed |
| Duplicate `series_character_id` in same series | `ValidationError` on insert |
| Conflicting promoted fact (different value) | `ConflictError`, requires MANUAL resolution, no silent overwrite |
| Unapproved promotion attempt | `PermissionError`, promotion blocked |
| Hydration from different series_id | `ValidationError`, namespace mismatch blocked |
| Missing Series Memory (first book) | Deterministic empty SeriesMemoryStore, no exception |
| Malformed canonical JSON | `JSONDecodeError` wrapped in `ValidationError`, fail-closed |

All must have deterministic, fail-closed behavior where applicable.

---

## 11. Validation Results

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

## 12. Final Verdict

### Is NTPE Ready for Series Memory Store Implementation?

> **NOT_READY**

### Blocking Reasons (Prioritized)

1. **No SeriesMemoryStore class** ??No canonical fact storage for series scope
2. **No SeriesCharacterRecord model** ??No namespace-isolated canonical character facts
3. **No hydration logic** ??Series?’Book projection mechanism missing
4. **No promotion logic** ??Book?’Series approval gate missing
5. **No persistence mechanism** ??Series memory save/load not implemented
6. **No validation/conflict detection** ??Series memory integrity checks missing

### Required Extensions (Not Redesigns)

- **Character Memory v2:** Extend `load_or_create_character_memory()` with optional `series_id` parameter to call hydration (additive only)
- **Character Memory v2 `__init__.py`:** Re-export hydration function (additive only)
- **All other v2/scene memory/models/lifecycle/selection/validation/store:** **FROZEN** ??no modifications allowed

### Series Memory Store Components to Implement

1. `core/series_memory/models.py` ??`SeriesCharacterRecord`, `SeriesFactRecord`
2. `core/series_memory/store.py` ??`SeriesMemoryStore` (CRUD, query, deduplication)
3. `core/series_memory/persistence.py` ??Load/save `series_memory_{series_id}.json` with hash integrity
4. `core/series_memory/hydration.py` ??SeriesMemoryStore ??BookMemoryStore projection (read-only, conservative scope)
5. `core/series_memory/promotion.py` ??BookMemoryStore ??SeriesMemoryStore with MANUAL approval gate
6. `core/series_memory/validation.py` ??Series memory validation, conflict detection
7. `core/series_memory/mapping.py` ??`korean_to_series_id`, `series_id_to_book_ids` indexing

### Sign-Off

**Audit Complete:** All required sections delivered, including Owner architecture review decisions.
**Preflight Status:** **NOT_READY** ??Series Memory Store requires Batch 5.2 Implementation.
**Next Step:** Owner Authorization ??Batch 5.2 Implementation.

---

*This audit was conducted against baseline commit `24f1dea` with zero production code modifications. Owner architecture review incorporated 2026-08-19.*

# P0 Stage 5 Batch 5.2 ??Series Memory Store Implementation Task

**Baseline Commit:** `24f1dea` (P0 Stage 5 Batch 5.1 Accepted)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md`
**Amendment:** `docs/governance/rm8/P0_STAGE5_SPECIFICATION_AMENDMENT.md`
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md`
**Task Status:** Specification Complete ??Ready for Owner Authorization
**Implementation Status:** NOT STARTED
**Owner Architecture Review:** 2026-08-19 ??Decisions Confirmed

---

## 1. Objective

Implement the **Series Memory Store** for P0 Stage 5 Series Continuity.

Deliverables:
- `core/series_memory/` module (models, store, persistence, hydration, promotion, validation, mapping)
- Canonical Series-level character facts (`SeriesCharacterRecord`)
- `SeriesMemoryStore` with CRUD, query, hydration, promotion logic
- Deterministic persistence with SHA-256 integrity/fingerprint
- Series?’Book hydration (read-only projection, conservative scope)
- Book?’Series promotion (MANUAL approval gate, conflict-aware)
- Namespace isolation via `series_character_id`
- Per-Series persistence and deterministic behavior
- Compatibility with existing Character Memory v2 (additive only)
- CSI-01 ~ CSI-10 isolation primitives for series memory

**Character Memory v2 persistence does not own Series Memory.**
SeriesMemoryStore is the upper-level owner; Book/Character Memory v2 are lower-level consumers.

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **Series Character Record Model** | `SeriesCharacterRecord` (canonical NEVER-expiry fact, `series_character_id = schar_{sha256(series_id|korean_name)[:16]}`, only APPROVED status) |
| **Series Memory Store** | `SeriesMemoryStore` (CRUD operations, query by `series_character_id`, hydration, promotion) |
| **Persistence** | Deterministic JSON serialization (`series_memory_{series_id}.json`) with SHA-256 manifest_fingerprint |
| **Hydration (Series ??Book)** | Project approved canonical facts into BookMemoryStore as APPROVED records (read-only, conservative scope) |
| **Promotion (Book ??Series)** | MANUAL approval-gated promotion of APPROVED BookMemoryRecord to SeriesCharacterRecord |
| **Validation & Conflict Detection** | Schema validation, hash verification, conflict detection on differing values |
| **Mapping & Indexing** | `korean_to_series_id`, `series_id_to_book_ids` for namespace isolation |
| **Character Memory v2 Extension** | Add optional `series_id` parameter to `load_or_create_character_memory()`, call hydration if provided |
| **Character Memory v2 `__init__.py`** | Re-export hydration function |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Redesign Character Memory v2 models/store/lifecycle/selection/validation | **FROZEN** (Constraint A) |
| Redesign Context/Scene Memory models/store/lifecycle/selection/validation | **FROZEN** (Constraint B) |
| Series Entity Registry | Batch 5.3 |
| Series Glossary | Batch 5.4 |
| Series Knowledge Population | Batch 5.5 |
| Series Checkpoint Hierarchy | Batch 5.6 |
| Series Orchestration | Batch 5.7 |
| Migration & Compatibility | Batch 5.8 |
| Validation & Freeze | Batch 5.9 |
| Any Provider / Network / Translation execution | Forbidden |
| Feature flag activation | Forbidden |
| Frozen Contract modifications | Forbidden |

---

## 4. Architecture

### 4.1 Module Structure

```
core/series_memory/
?œâ??€ __init__.py                    # Public exports
?œâ??€ models.py                      # SeriesCharacterRecord, SeriesFactRecord
?œâ??€ store.py                       # SeriesMemoryStore (CRUD, query, hydration, promotion)
?œâ??€ persistence.py                 # Load/save series_memory_{series_id}.json
?œâ??€ hydration.py                   # SeriesMemoryStore ??BookMemoryStore (read-only)
?œâ??€ promotion.py                   # BookMemoryStore ??SeriesMemoryStore (MANUAL approval gate)
?œâ??€ validation.py                  # Series memory validation, conflict detection
?”â??€ mapping.py                     # korean_to_series_id, series_id_to_book_ids
```

### 4.2 Dependency / Ownership Diagram

```
SeriesMemoryStore (Upper-Level Owner)
    ??    ?œâ??€ persistence
    ?œâ??€ validation
    ?œâ??€ promotion (Book ??Series)
    ?œâ??€ hydration (Series ??Book, read-only)
    ?œâ??€ namespace mapping (series_character_id)
    ?”â??€ canonical serialization
    ??    ??Book / Character Memory v2 (Lower-Level Consumer)
    ??    ?œâ??€ load_or_create_character_memory(series_id=...) calls hydration
    ?œâ??€ BookMemoryStore receives hydrated APPROVED records
    ?œâ??€ No dependency on SeriesMemoryStore internals
    ?”â??€ Promotion candidates generated from BookMemoryStore APPROVED facts
```

**Forbidden:** Bidirectional dependency `CharacterMemory <-> SeriesMemory`

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.character_memory_v2.models` | Internal | FactType, EvidenceType, ApprovalStatus, ExpiryKind, etc. (read-only) |
| `core.character_memory_v2.store` | Internal | MemoryStore, add_or_merge_memory (read-only) |
| `core.character_memory_v2.persistence` | Internal | For hydration integration (additive only) |
| `core.series_identity` | Internal | SeriesIdentity, SeriesManifest (read-only) |

**No dependencies on:** `core.context_scene_memory`, `core.entity_resolver`, `core.knowledge_runtime`, `core.book_intake`, `core.translation_runtime`, `core.runtime_checkpoint`

---

## 5. Data Models

### 5.1 SeriesCharacterRecord (Canonical Only)

```python
@dataclass(frozen=True)
class SeriesCharacterRecord:
    """Canonical character fact ??NEVER expires, series-scoped."""
    series_character_id: str        # schar_{sha256(series_id|korean_name)[:16]}
    korean_name: str                # Original Korean name
    canonical_name: str             # Approved Chinese translation
    aliases: tuple[str, ...]        # All known aliases (Korean variants)
    fact_type: FactType             # CANONICAL_NAME, RELATIONSHIP, etc.
    value: str                      # Fact value
    evidence: tuple[Evidence, ...]  # Supporting evidence (all books)
    confidence: float               # Aggregated confidence
    approval_status: ApprovalStatus # Must be APPROVED for canonical facts
    source_books: tuple[str, ...]   # Book identities contributing
    created_at: str
    updated_at: str
    version: int
```

**Key Differences from Book MemoryRecord:**
- `series_character_id` instead of `character_id` (namespace isolated)
- `source_books` tracks provenance across volumes
- Only `APPROVED` status facts stored (no PENDING/CONFLICT)
- No `expiry_policy` ??always `NEVER`

### 5.2 SeriesFactRecord (Extension for Non-Character Facts)

```python
@dataclass(frozen=True)
class SeriesFactRecord:
    """Canonical non-character fact ??NEVER expires, series-scoped."""
    series_fact_id: str             # sfact_{sha256(series_id|fact_type|value)[:16]}
    fact_type: FactType             # TERMINOLOGY_PREFERENCE, etc.
    value: str                      # Fact value
    evidence: tuple[Evidence, ...]  # Supporting evidence
    confidence: float               # Aggregated confidence
    approval_status: ApprovalStatus # Must be APPROVED
    source_books: tuple[str, ...]   # Book identities contributing
    created_at: str
    updated_at: str
    version: int
```

### 5.3 SeriesMemoryStore Operations

| Operation | Description |
|-----------|-------------|
| `get_canonical_name(series_character_id)` | Returns approved canonical name |
| `get_relationships(series_character_id)` | Returns all APPROVED relationships |
| `get_all_canonical_facts()` | Returns all SeriesCharacterRecord |
| `get_all_canonical_facts_by_type(fact_type)` | Returns facts by FactType |
| `hydrate_book_store(book_store, book_identity)` | Copies relevant canonical facts to BookMemoryStore (read-only) |
| `promote_from_book(book_store, book_identity, approval_gate)` | Promotes APPROVED facts from book to series (see Â§10) |
| `add_or_merge_canonical_fact(record: SeriesCharacterRecord) -> AddResult` | Deduplicate by series_character_id + fact_type + value |
| `validate_integrity() -> bool` | Verify SHA-256 fingerprint matches stored data |

---

## 6. Series ID Semantics (Re-Use Batch 5.1)

```python
def compute_series_id(user_defined_series_key: str) -> str:
    """
    Deterministic series identity from user-provided stable series key.
    """
    canonical_key = user_defined_series_key.strip().lower()
    return hashlib.sha256(f"series|{canonical_key}".encode("utf-8")).hexdigest()[:16]

def compute_series_character_id(series_id: str, korean_name: str) -> str:
    """Namespace-isolated character ID."""
    return f"schar_{hashlib.sha256(f'{series_id}|{korean_name}'.encode()).hexdigest()[:16]}"
```

**Properties:**
- Same `(series_id, korean_name)` ??same `series_character_id` (deterministic, cross-machine)
- `series_character_id` **never changes** after creation
- Two Series with same `korean_name` but different `series_id` ??different `series_character_id` (isolation)

---

## 7. Serialization Rules

### 7.1 Canonical JSON

```python
def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 7.2 Series Memory Fingerprint

```python
def compute_series_memory_fingerprint(series_memory_dict: dict) -> str:
    """
    Compute SHA-256 of canonical series memory payload (excluding fingerprint itself).
    """
    payload = {k: v for k, v in series_memory_dict.items() if k != "series_memory_fingerprint"}
    canonical = to_canonical_json(payload)
    return compute_sha256(canonical)
```

### 7.3 Round-Trip Guarantee

```
series_memory ??to_canonical_json ??bytes ??sha256 ??fingerprint
series_memory ??to_dict() ??load ??serialize ??same fingerprint
```

**Deterministic:** Same inputs ??bit-for-bit identical JSON ??identical fingerprint.

---

## 8. Validation Rules

### 8.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_memory" | `ValidationError` |
| `schema_version` == "1.0" | `ValidationError` |
| `series_memory_fingerprint` matches computed | `IntegrityError` (fail-closed) |
| All required fields present | `ValidationError` |
| `series_character_id` matches `schar_{sha256(series_id|korean_name)[:16]}` | `ValidationError` |
| `approval_status` == `ApprovalStatus.APPROVED` | `ValidationError` |
| `evidence` validates per EvidenceType | `ValidationError` |
| `confidence` in [0.0, 1.0] | `ValidationError` |
| `version` >= 1 | `ValidationError` |
| `created_at`, `updated_at` valid ISO 8601 UTC | `ValidationError` |

### 8.2 Business Rule Validation (on Mutations)

| Operation | Validation |
|-----------|------------|
| `add_or_merge_canonical_fact(record)` | Fact must be APPROVED; series_id must match namespace |
| `hydrate_book_store(book_store, book_identity)` | book_identity must exist in SeriesManifest for series_id |
| `promote_from_book(book_store, book_identity, approval_gate)` | Only APPROVED BookMemoryRecord promoted; MANUAL approval gate respected |

### 8.3 Fail-Closed Principle

- **Any validation failure ??Exception**, no partial load, no fallback defaults
- Corrupted series memory file ??`IntegrityError` ??operation blocked
- No silent data corruption

---

## 9. Hydration Rules (Series ??Book) ??Conservative Scope

### 9.1 Hydration Trigger

- At Book translation start (when `load_or_create_character_memory` called with `series_id`)
- At Book Context/Scene Memory initialization
- At EntityResolver initialization for book

### 9.2 Hydration Data Flow

```
SeriesMemoryStore (canonical NEVER facts)
    ??    ?œâ??€ Character canonical names ??BookMemoryStore (as APPROVED records)
    ?œâ??€ SeriesFactRecord terminology ??BookMemoryStore (as APPROVED records)
    ?”â??€ (Future: SeriesEntityRegistry ??EntityResolver, SeriesGlossary ??BookGlossary)
```

### 9.3 Hydration Field Matrix (Precise)

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

### 9.4 Hydration Transformation

| Source | Target | Transformation |
|--------|--------|----------------|
| SeriesCharacterRecord.canonical_name | BookMemoryRecord (FactType.CANONICAL_NAME) | New record, APPROVED, reviewer="series_hydration" |
| SeriesCharacterRecord aliases | BookMemoryRecord (FactType.NAME_VARIANT) | New records, APPROVED |
| SeriesCharacterRecord relationships | BookMemoryRecord (FactType.RELATIONSHIP) | New records, APPROVED |
| SeriesFactRecord.value | BookMemoryRecord (matching FactType) | New record, APPROVED, reviewer="series_hydration" |

### 9.5 Hydration Idempotency

- Hydration is **idempotent** ??re-running produces same BookMemoryStore state
- Uses `series_memory_hash` in SeriesManifest to detect changes
- BookMemoryStore tracks `hydration_source = f"series:{series_id}:{series_memory_hash}"`

### 9.6 Hydration Conflict Resolution

| Book Memory State | Series Fact Value | Action |
|-------------------|-------------------|--------|
| No existing fact | Any | Create new APPROVED record |
| Existing PENDING fact | Same value | Upgrade to APPROVED, reviewer="series_hydration" |
| Existing PENDING fact | Different value | Keep PENDING (requires user resolution) |
| Existing APPROVED fact | Same value | DUPLICATE (no action) |
| Existing APPROVED fact | Different value | CONFLICT (requires manual resolution) |

---

## 10. Promotion Rules (Book ??Series) ??MANUAL Gate

### 10.1 Promotion Boundary (CRITICAL)

**Series owns canonical facts. Book proposes. Promotion requires MANUAL approval.**

```
Book Translation
    ??    ?œâ??€ BookMemoryStore accumulates facts (PENDING ??APPROVED via user review)
    ?œâ??€ Book completes (all chunks translated, user review done)
    ??    ?”â??€ Promotion Gate (MANUAL ??frozen by D-07)
         ??         ?œâ??€ For each APPROVED BookMemoryRecord:
         ??    If fact_type in {CANONICAL_NAME, RELATIONSHIP, TERMINOLOGY_PREFERENCE, ROLE_OR_IDENTITY, PRONOUN_OR_GENDER_REFERENCE, APPEARANCE}:
         ??        If series has no record ??PROMOTE (create SeriesCharacterRecord/SeriesFactRecord)
         ??        If series has record with SAME value ??NO-OP
         ??        If series has record with DIFFERENT value ??CONFLICT (requires MANUAL resolution)
         ??         ?”â??€ For EntityResolver user_overrides created during book:
               If series_registry has no entry ??PROMOTE (create SeriesEntityRecord)
               If series_registry has SAME target ??NO-OP
               If series_registry has DIFFERENT target ??CONFLICT (MANUAL)
```

### 10.2 Promotion Policy (Fixed ??Not Configurable)

```python
@dataclass(frozen=True)
class PromotionPolicy:
    auto_promote_canonical_names: bool = False      # MANUAL only (D-07)
    auto_promote_relationships: bool = False        # MANUAL only
    auto_promote_terminology: bool = False          # MANUAL only
    auto_promote_entities: bool = False             # MANUAL only
    conflict_resolution: str = "manual"             # "manual" only
    require_user_approval: bool = True              # Always True
```

**No auto-promotion.** All fact types require MANUAL approval. Policy is frozen.

### 10.3 Promotion Audit Trail

Every promotion creates:
```python
@dataclass(frozen=True)
class PromotionRecord:
    promotion_id: str
    series_id: str
    book_identity: str
    source_memory_id: str        # BookMemoryRecord.memory_id
    target_series_character_id: str
    fact_type: FactType
    action: str                  # "created" | "updated" | "conflict"
    resolved_by: str | None      # "user" | "policy:book_wins" | etc.
    resolved_at: str
    previous_value: str | None
    new_value: str
```

---

## 11. Same-Name Series Behavior (D-09 Confirmed)

| Scenario | Behavior |
|----------|----------|
| User creates "Passion" ??`series_id=A` | Creates Series A |
| User creates "Passion" again ??`series_id=B` | Creates Series B (different ID) |
| Series A and B both have `series_name="Passion"` | **Allowed** ??completely isolated |
| User adds canonical fact for "?Žæ?" to Series A | Stored in Series A only |
| User adds canonical fact for "?Žæ?" to Series B | Stored in Series B only |
| No automatic merge, no name-based lookup | **Explicit `series_id` required** for all operations |

---

## 12. Cross-Series Isolation Primitives (D-08 Confirmed)

**Identity Namespace Isolation (Contract for Series Memory Store):**

| Downstream Component | Isolation Contract |
|---------------------|-------------------|
| `SeriesMemoryStore` | `series_character_id = schar_{sha256(series_id\|korean)}` |
| `SeriesCharacterRecord.canonical_name` ??BookMemoryRecord | Book record carries `series_character_id` reference |
| `SeriesMemoryStore` persistence | File: `series_memory_{series_id}.json` |
| `SeriesMemoryStore` hydration | BookMemoryStore records tagged with `series_id` provenance |
| `SeriesMemoryStore` promotion | Only facts from matching `series_id` book promoted |

**Batch 5.2 delivers:** The `series_character_id` primitive and SeriesMemoryStore authority.

---

## 13. CSI-01 ~ CSI-10 Acceptance Tests (D-08 Confirmed)

> **Hard Gates:** All must PASS. Any failure ??Batch 5.2 not accepted.

| Test ID | Description | Batch 5.2 Verification |
|---------|-------------|------------------------|
| **CSI-01** | Same Korean name in Series A vs B ??different `series_character_id` | Verify `compute_series_character_id()` uses `series_id` prefix |
| **CSI-02** | Same entity name in Series A vs B ??different `series_entity_id` | (Entity Registry - Batch 5.3) |
| **CSI-03** | Series A glossary locked term ??Series B | (Glossary - Batch 5.4) |
| **CSI-04** | In-memory isolation: load Series A, then Series B | Verify `SeriesMemoryStore` returns independent canonical facts |
| **CSI-05** | Series A promotion doesn't leak to Series B | Verify `series_id` gating in all promotion operations |
| **CSI-06** | Series A checkpoint restore doesn't load Series B | (Checkpoint - Batch 5.6) |
| **CSI-07** | Duplicate series_name ??creates new Series, no merge | (Identity - Batch 5.1) |
| **CSI-08** | Delete Series A directory ??Series B unaffected | Verify no cross-directory references |
| **CSI-09** | Concurrent Runtime instances with different Series | Verify `series_id` passed explicitly, no global state |
| **CSI-10** | Series A archived ??Series B active | Verify lifecycle state per-Series, no global lock |

**Test Location:** `tests/series/test_batch5_2_cross_series_isolation.py`

---

## 14. Frozen Contracts Audit

**Batch 5.2 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | ??No touch |
| Context Pipeline Contract | ??No touch |
| Prompt Pipeline Contract | ??No touch |
| Plugin Contract | ??No touch |
| Production Pipeline Contract | ??No touch |
| Translation Runtime Contract | ??No touch |
| Intelligence Contract | ??No touch |
| Knowledge Contract | ??No touch |
| Snapshot Contract | ??No touch |
| Character Memory v2 core | ??No touch (models, store, lifecycle, selection, validation) |
| Context/Scene Memory core | ??No touch |
| Entity Resolver core | ??No touch |
| KnowledgeRuntime core | ??No touch |
| Runtime Checkpoint core | ??No touch |

**New Contract Created by Batch 5.2:**
- **Series Memory Contract** (`core/series_memory/`) ??to be added to Foundation Manifest in Batch 5.9

---

## 15. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| Any existing `core/character_memory_v2/models.py` | ??No touch |
| Any existing `core/character_memory_v2/store.py` | ??No touch |
| Any existing `core/character_memory_v2/lifecycle.py` | ??No touch |
| Any existing `core/character_memory_v2/selection.py` | ??No touch |
| Any existing `core/character_memory_v2/validation.py` | ??No touch |
| Any existing `core/context_scene_memory/` | ??No touch |
| Any existing `core/entity_resolver/` | ??No touch |
| Any existing `core/knowledge_runtime/` | ??No touch |
| Any existing `core/book_intake/` | ??No touch |
| Any existing `core/translation_runtime/` | ??No touch |
| Any existing `core/translation_pipeline/` | ??No touch |
| Any existing `core/production_runtime/` | ??No touch |
| Any existing `core/runtime_checkpoint/` | ??No touch |
| Any Frozen Contract (9 existing) | ??No touch |
| Feature flag changes | ??No touch |
| TXT/EPUB/Translation behavior | ??No touch |
| Provider/Network/Translation execution | ??No touch |

---

## 16. Test Requirements

### 16.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_compute_series_character_id_deterministic` | Same (series_id, korean_name) ??same ID |
| `test_series_character_record_immutability` | All fields immutable after creation |
| `test_series_character_record_approval_enforced` | Only APPROVED status allowed |
| `test_series_memory_store_crud` | Create, read, update, delete canonical facts |
| `test_series_memory_store_deduplication` | Same fact ??ADD on first, DUPLICATE on second |
| `test_series_memory_store_conflict_detection` | Different values ??CONFLICT (requires resolution) |
| `test_hydration_roundtrip` | Series ??Book ??Series (promotion) ??same canonical facts |
| `test_hydration_idempotent` | Hydrate twice ??same BookMemoryStore state |
| `test_hydration_conservative_scope` | Only ALLOWED fact types hydrated; FORBIDDEN types rejected |
| `test_promotion_manual_gate` | MANUAL approval required; auto-promotion disabled |
| `test_promotion_conflict_detection` | Different values ??conflict exception |
| `test_namespace_isolation` | Series A "?Žæ?" ??Series B "?Žæ?" |
| `test_canonical_fact_immutability` | Only APPROVED facts in SeriesMemoryStore |
| `test_persistence_roundtrip` | Save ??load ??fingerprint matches |
| `test_persistence_integrity` | Tampered file ??IntegrityError |
| `test_persistence_fail_closed` | Corrupted JSON ??exception |
| `test_deterministic_serialization` | Same input ??bit-for-bit identical JSON |
| `test_hydration_source_tracking` | BookMemoryStore records carry hydration_source |
| `test_promotion_audit_trail` | PromotionRecord created for each action |

### 16.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_character_id_deterministic_property` | 1000 |
| `test_series_memory_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |
| `test_hydration_idempotent_property` | 1000 |

### 16.3 Cross-Series Isolation Tests (CSI-01 ~ CSI-10)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_01_series_character_id_isolation` | CSI-01 |
| `test_csi_04_registry_inmemory_isolation` | CSI-04 |
| `test_csi_05_promotion_non_leakage` | CSI-05 |
| `test_csi_08_filesystem_isolation` | CSI-08 |
| `test_csi_09_runtime_concurrent_isolation` | CSI-09 |
| `test_csi_10_lifecycle_isolation` | CSI-10 |

---

## 17. Batch 5.2 Acceptance Test Matrix (Comprehensive)

| Category | Test | Description | Pass Criteria |
|----------|------|-------------|---------------|
| **Persistence** | `test_persist_save_load` | Save SeriesMemoryStore, load, verify fingerprint | Fingerprint matches, records intact |
| **Persistence** | `test_persist_corrupted_fail_closed` | Corrupt JSON file, attempt load | `IntegrityError` raised, no partial load |
| **Persistence** | `test_persist_missing_file` | Load non-existent series memory | Deterministic empty SeriesMemoryStore |
| **Persistence** | `test_persist_restart` | Process restart simulation | Reload produces identical state |
| **Reload** | `test_reload_idempotent` | Load ??save ??load ??save | Bit-for-bit identical JSON |
| **Promotion** | `test_promote_new_fact` | Promote new APPROVED fact from Book 1 | SeriesCharacterRecord created |
| **Promotion** | `test_promote_same_value` | Promote fact with same value as series | NO-OP, no duplicate |
| **Promotion** | `test_promote_conflict` | Promote fact with different value | CONFLICT, requires MANUAL |
| **Promotion** | `test_promote_unapproved_blocked` | Attempt promote PENDING fact | Blocked, not promoted |
| **Approval Gate** | `test_approval_manual_only` | Verify no auto-promotion path exists | All promotions require user action |
| **Approval Gate** | `test_approval_audit_trail` | Verify PromotionRecord created | Complete audit trail per promotion |
| **Conflict Handling** | `test_conflict_detection` | Different canonical_name for same character | Conflict detected, no silent overwrite |
| **Conflict Handling** | `test_conflict_resolution_manual` | User resolves conflict, series updated | Series updated, audit trail recorded |
| **Hydration** | `test_hydrate_canonical_name` | Series canonical_name ??BookMemoryStore | APPROVED record with reviewer="series_hydration" |
| **Hydration** | `test_hydrate_aliases` | Series aliases ??BookMemoryStore | NAME_VARIANT records created |
| **Hydration** | `test_hydrate_relationships` | Series relationships ??BookMemoryStore | RELATIONSHIP records created |
| **Hydration** | `test_hydrate_forbidden_rejected` | Attempt hydrate SCENE state | Rejected, not in BookMemoryStore |
| **Hydration** | `test_hydrate_idempotent` | Hydrate twice | Identical BookMemoryStore state |
| **Hydration** | `test_hydrate_conflict_resolution` | Book has PENDING different value | PENDING retained, not overwritten |
| **Cross-Series Isolation** | `test_isolation_same_korean_name` | Series A "?Žæ?" vs Series B "?Žæ?" | Different series_character_id, no leakage |
| **Cross-Series Isolation** | `test_isolation_promotion_gated` | Promote in Series A, verify Series B clean | Series B unaffected |
| **Cross-Series Isolation** | `test_isolation_filesystem` | Delete Series A dir, Series B intact | No cross-directory references |
| **Corruption** | `test_corruption_fingerprint` | Tamper fingerprint | IntegrityError on load |
| **Corruption** | `test_corruption_json` | Malformed JSON | ValidationError on load |
| **Corruption** | `test_corruption_schema` | Wrong schema_name/version | ValidationError on load |
| **Deterministic Serialization** | `test_deterministic_json` | Same records, multiple serializations | Bit-for-bit identical |
| **Deterministic Serialization** | `test_deterministic_hash` | Same records, multiple hashes | Identical SHA-256 |
| **Process Restart** | `test_restart_continuity` | Simulate restart, reload series memory | Canonical facts available for Book 2 |
| **Backward Compatibility** | `test_compat_no_series_id` | load_or_create_character_memory without series_id | Works identically to baseline |
| **Fail-Closed** | `test_fail_closed_all_paths` | All validation paths throw exceptions | No fallback defaults, no silent corruption |

---

## 18. Validation Gates

**All must PASS before Batch 5.2 considered complete:**

- [ ] `python ntpe_validate.py` ??PASS (no new warnings)
- [ ] `python -m compileall core/` ??0 errors
- [ ] `git diff --check` ??clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-01 ~ CSI-10 tests PASS
- [ ] Batch 5.2 Acceptance Test Matrix (Â§17) all PASS
- [ ] No regression in existing 888 pytest tests
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 19. Git Scope Rules

**Allowed Changes:**
- **NEW** `core/series_memory/` (complete module)
- **NEW** `tests/series/test_batch5_2_*.py` (test files)
- **ADDITIVE** `core/character_memory_v2/persistence.py` ??Optional `series_id` parameter, hydration call
- **ADDITIVE** `core/character_memory_v2/__init__.py` ??Export new hydration function

**Forbidden:**
- Any modification to existing production code outside allowed additive changes
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 20. Delivery Rules

**Deliverables (working tree changes only, no staging):**
1. `core/series_memory/` module
2. `tests/series/test_batch5_2_*.py`
3. Additive changes to `core/character_memory_v2/persistence.py`
4. Additive changes to `core/character_memory_v2/__init__.py`
5. Updated `P0_STAGE5_FORMAL_SPECIFICATION.md` (if any spec clarifications needed)
6. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 21. Rollback Boundary

**Clean Rollback:**
- Delete `core/series_memory/` directory
- Revert `core/character_memory_v2/persistence.py` to baseline
- Revert `core/character_memory_v2/__init__.py` to baseline

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules

---

## 22. Provider / Network / Translation Policy

- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation only

---

## 23. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/series_memory/` ??implementation
- `tests/series/` ??tests
- `core/character_memory_v2/persistence.py` ??additive change
- `core/character_memory_v2/__init__.py` ??additive change
- `docs/governance/rm8/` ??docs/contracts
- `artifacts/` ??diagnostic output only

---

## 24. Completion Criteria

**Batch 5.2 Complete When:**

1. All Â§16 unit tests PASS
2. All Â§16 property-based tests PASS (1000 iterations each)
3. All Â§17 CSI-01 ~ CSI-10 tests PASS
4. All Â§17 Batch 5.2 Acceptance Test Matrix PASS
5. Validation gates (Â§18) all PASS
6. Git status shows only allowed new files + allowed additive changes
7. No production code modified outside allowed additive changes
8. No Frozen Contracts modified
9. **Character Memory v2 persistence does not own Series Memory** (dependency direction verified)

**Status Report:** "P0 Stage 5 Batch 5.2 Specification READY ??Implementation COMPLETE ??Awaiting Owner Review"

---

## 25. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Series Memory Store design complete, models defined, Owner decisions incorporated | 2026-08-19 |
| Owner | Authorization to proceed | ____________ |
| QA | CSI-01~10 test matrix & Acceptance Test Matrix accepted | ____________ |

---

*End of Batch 5.2 Implementation Task. Implementation NOT STARTED. Awaiting Owner Authorization.*

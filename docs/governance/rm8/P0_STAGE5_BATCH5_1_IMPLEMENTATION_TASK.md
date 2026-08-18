# P0 Stage 5 Batch 5.1 — Series Identity & Manifest Implementation Task

**Baseline Commit:** `4b7b8781bae035466dc215ca0a265052f0055cda` (P0 Stage 4 Final Delivery)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md`
**Amendment:** `docs/governance/rm8/P0_STAGE5_SPECIFICATION_AMENDMENT.md`
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md`
**Task Status:** Specification Complete — Ready for Owner Authorization
**Implementation Status:** NOT STARTED

---

## 1. Objective

Establish the **Series Identity & Manifest** foundation for P0 Stage 5 Series Continuity.

Deliverables:
- `core/series_identity/` module (identity, manifest, registry, persistence, validation)
- Deterministic Series ID from user-provided stable key
- Series Manifest with book membership, ordering, lifecycle
- Series artifact namespace isolation
- CSI-01 ~ CSI-10 identity/manifest contract primitives

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **Series Identity Model** | `SeriesIdentity` (immutable `series_id`, mutable `series_name`, timestamps) |
| **Series Manifest Model** | `SeriesManifest` with books[], lifecycle_status, derived hashes |
| **Series Book Entry** | `SeriesBookEntry` (volume_number, book_identity, source_path, title, status, fingerprints) |
| **Series Lifecycle** | CREATED → ACTIVE → COMPLETED → ARCHIVED (state machine) |
| **Series Registry** | `SeriesRegistry.create()`, `get()`, `list()`, `add_book()`, `update_name()`, `archive()` |
| **Persistence** | `series_manifest_{series_id}.json` in `output/series/{series_id}/` |
| **Serialization** | Canonical JSON (sorted keys, no whitespace) + SHA-256 manifest_fingerprint |
| **Validation** | Schema validation, hash verification, fail-closed on corruption |
| **Same-Name Series Isolation** | Duplicate `series_name` allowed with different `series_id`; no auto-merge |
| **Cross-Series Identity Primitives** | `series_id` namespace isolation for all downstream contracts |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Character Memory Series persistence | Batch 5.2 |
| Context/Scene Memory Series persistence | Not applicable (Context is book-local) |
| Series Entity Registry | Batch 5.3 |
| Series Glossary | Batch 5.4 |
| Series Knowledge Population | Batch 5.5 |
| Series Checkpoint hierarchy | Batch 5.6 |
| Memory hydration (Series → Book) | Batch 5.2 |
| Memory promotion (Book → Series) | Batch 5.2+ (default MANUAL, not implemented here) |
| SeriesOrchestrator / Coordinator | Batch 5.7 |
| User-facing multi-book translation workflow | Batch 5.7 |
| RuntimeOrchestrator Series behavior | Batch 5.7 |
| Archive/legacy cleanup | Not in Stage 5 |
| Any Provider / Network / Translation execution | Forbidden |
| Feature flag activation | Forbidden |
| Frozen Contract modifications | Forbidden |

---

## 4. Architecture

### 4.1 Module Structure

```
core/series_identity/
├── __init__.py                    # Public exports
├── identity.py                    # SeriesIdentity, compute_series_id()
├── manifest.py                    # SeriesManifest, SeriesBookEntry, SeriesLifecycle
├── registry.py                    # SeriesRegistry (create, get, list, add_book, etc.)
├── persistence.py                 # Load/save series_manifest_{series_id}.json
├── validation.py                  # Schema validation, hash verification
├── canonical.py                   # Canonical JSON + SHA-256 fingerprint
└── contract.py                    # Contract constants (schema_name, schema_version)
```

### 4.2 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.book_intake.manifest.BookIntakeManifest` | Internal | For `book_identity` + `manifest_fingerprint` reference |
| `core.foundation.manifest.validate_foundation_manifest` | Internal | Contract registration (future) |

**No dependencies on:** `core.character_memory_v2`, `core.context_scene_memory`, `core.entity_resolver`, `core.knowledge_runtime`, `core.translation_runtime`, `core.runtime_checkpoint`

---

## 5. Data Models

### 5.1 SeriesIdentity

```python
@dataclass(frozen=True)
class SeriesIdentity:
    series_id: str              # Immutable, from compute_series_id()
    series_name: str            # Mutable display name
    created_at: str             # ISO 8601 UTC (e.g., "2026-08-18T00:00:00Z")
    updated_at: str             # ISO 8601 UTC, updated on name change
```

| Field | Mutability | Source |
|-------|------------|--------|
| `series_id` | **IMMUTABLE** | `compute_series_id(canonical_key)` |
| `series_name` | **MUTABLE** | User input (display) |
| `created_at` | **IMMUTABLE** | System timestamp at creation |
| `updated_at` | **AUTO** | System timestamp on any change |

### 5.2 SeriesLifecycle

```python
class SeriesLifecycle(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
```

**State Machine (D-04 Confirmed):**

```
CREATED --add_book(first)--> ACTIVE --all promoted, no in_progress--> COMPLETED --archive--> ARCHIVED
     |                           |                                        |
     |                           --archive (user)-->                     |
     +------------------------------------------------------------------------>
```

| Transition | Trigger | Actor |
|------------|---------|-------|
| CREATED → ACTIVE | First `add_book()` | User (via Registry) |
| ACTIVE → COMPLETED | All books promoted, no `in_progress` | System (auto-evaluated) |
| ACTIVE → ARCHIVED | `SeriesRegistry.archive(series_id)` | User |
| COMPLETED → ARCHIVED | `SeriesRegistry.archive(series_id)` | User |

**No SUSPENDED state.** Book-level control is sufficient.

### 5.3 SeriesBookEntry

```python
@dataclass(frozen=True)
class SeriesBookEntry:
    volume_number: int              # Sequential 1-based, IMMUTABLE
    book_identity: str              # Stage 4 Book ID, IMMUTABLE
    source_path: str                # Original path at add-time, IMMUTABLE
    title: str                      # Display title, MUTABLE
    status: BookStatus              # STATE_MACHINE
    content_fingerprint: str        # SHA256 of source file content, IMMUTABLE
    manifest_fingerprint: str       # BookIntakeManifest fingerprint, IMMUTABLE
    added_at: str                   # ISO timestamp, IMMUTABLE
    completed_at: str | None        # ISO timestamp, set when status=completed
    promoted_at: str | None         # ISO timestamp, set when status=promoted
```

**BookStatus (within Series Manifest):**

```python
class BookStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PROMOTED = "promoted"
    ARCHIVED = "archived"
    FAILED = "failed"
```

**State Machine:**

```
PENDING --translate start--> IN_PROGRESS --translate done--> COMPLETED --promote--> PROMOTED
                    ↘ FAILED
COMPLETED/PROMOTED/FAILED --archive--> ARCHIVED
```

### 5.4 SeriesManifest

```python
@dataclass(frozen=True)
class SeriesManifest:
    schema_name: str                    # "ntpe.series_manifest"
    schema_version: str                 # "1.0"
    series_id: str                      # IMMUTABLE
    series_name: str                    # MUTABLE
    lifecycle_status: SeriesLifecycle   # STATE_MACHINE
    created_at: str                     # IMMUTABLE
    updated_at: str                     # AUTO
    books: tuple[SeriesBookEntry, ...]  # APPEND-ONLY, ordered by volume_number
    series_memory_hash: str             # DERIVED (empty initially)
    series_checkpoint_hash: str         # DERIVED (empty initially)
    manifest_fingerprint: str           # DERIVED (SHA256 of canonical payload)
```

**Field Authority Summary:**

| Field | Authority | Mutability |
|-------|-----------|------------|
| `schema_name`, `schema_version` | Contract | IMMUTABLE |
| `series_id` | Creation | IMMUTABLE |
| `series_name` | User | MUTABLE |
| `lifecycle_status` | System | STATE_MACHINE |
| `created_at` | System | IMMUTABLE |
| `updated_at` | System | AUTO |
| `books[]` | Registry | APPEND-ONLY (entries IMMUTABLE) |
| `series_memory_hash` | System | DERIVED |
| `series_checkpoint_hash` | System | DERIVED |
| `manifest_fingerprint` | System | DERIVED |

---

## 6. Series ID Semantics (D-01, D-02 Confirmed)

```python
def compute_series_id(user_defined_series_key: str) -> str:
    """
    Deterministic series identity from user-provided stable series key.

    Canonicalization:
    - Strip leading/trailing whitespace
    - Lowercase (ASCII)
    - No other normalization (preserve Unicode as-is)
    """
    canonical_key = user_defined_series_key.strip().lower()
    return hashlib.sha256(f"series|{canonical_key}".encode("utf-8")).hexdigest()[:16]
```

**Properties:**
- Same canonical key → same `series_id` (deterministic, cross-machine)
- `series_id` **never changes** after creation
- `series_name` (display) can change independently
- Two Series with same `series_name` but different `series_id` are **completely isolated** (D-09)

---

## 7. Manifest Authority (D-03 Confirmed)

**Manifest is the single source of truth for:**
- Series identity (`series_id`)
- Series display name (`series_name`)
- Series lifecycle state
- Book membership & ordering (`volume_number`, `book_identity`)
- Authoritative metadata (timestamps, fingerprints)

**Derived/runtime state NEVER overwrites Manifest authority:**
- `series_memory_hash`, `series_checkpoint_hash`, `manifest_fingerprint` are **computed from** Manifest + data, not written back as authority
- Book runtime progress (`in_progress`, chunk index) stays in Book/Session checkpoints
- No reverse dependency from derived → authority

---

## 8. Book Membership & Ordering (D-03, D-09, D-10 Confirmed)

### 8.1 volume_number
- Sequential 1-based integer
- Assigned at `add_book()` time: `max(existing_volume_numbers) + 1`
- **IMMUTABLE** once assigned
- No gaps, no reordering, no deletion (only `archived` status)

### 8.2 book_identity
- **Stage 4 frozen definition** (D-10):
  ```python
  def compute_book_identity(input_path: Path, project_name: str) -> str:
      identity_source = f"{project_name}|{input_path.resolve()}"
      return hashlib.sha256(identity_source.encode("utf-8")).hexdigest()[:16]
  ```
- Referenced directly from `BookIntakeManifest`
- **IMMUTABLE** — even if file moves/renames

### 8.3 Duplicate Handling
- Same `book_identity` added to same Series → **REJECTED** (already member)
- Same `book_identity` in different Series → **ALLOWED** (different context via `volume_number` + `series_id`)
- Same `series_name` (different `series_id`) → **ALLOWED**, no auto-merge (D-09)

---

## 8. Artifact Layout (D-05 Confirmed)

```
output/
├── series/
│   └── {series_id}/
│       └── series_manifest_{series_id}.json    # Only file created in Batch 5.1
├── books/
│   └── {book_identity}/
│       ├── (existing Stage 4 artifacts)
└── translations/
    └── {book_identity}/
        └── (existing Stage 4 output)
```

**Isolation Rules:**
- Series artifacts **only** in `output/series/{series_id}/`
- Book artifacts **only** in `output/books/{book_identity}/`
- No cross-directory filesystem references
- All cross-references via explicit JSON identity fields

---

## 9. Serialization Rules

### 9.1 Canonical JSON

```python
def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 9.2 Manifest Fingerprint

```python
def compute_manifest_fingerprint(manifest_dict: dict) -> str:
    """
    Compute SHA-256 of canonical manifest payload (excluding manifest_fingerprint itself).
    """
    payload = {k: v for k, v in manifest_dict.items() if k != "manifest_fingerprint"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 9.3 Round-Trip Guarantee

```
manifest → to_canonical_json → bytes → sha256 → fingerprint
manifest → to_dict() → load → serialize → same fingerprint
```

**Deterministic:** Same inputs → bit-for-bit identical JSON → identical fingerprint.

---

## 10. Validation Rules

### 10.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_manifest" | `ValidationError` |
| `schema_version` == "1.0" | `ValidationError` |
| `series_id` matches filename | `ValidationError` |
| `manifest_fingerprint` matches computed | `IntegrityError` (fail-closed) |
| All required fields present | `ValidationError` |
| `volume_number` sequential, no gaps, starts at 1 | `ValidationError` |
| No duplicate `book_identity` in books[] | `ValidationError` |
| `lifecycle_status` valid enum | `ValidationError` |
| `books[].status` valid enum | `ValidationError` |
| Timestamps valid ISO 8601 UTC | `ValidationError` |

### 10.2 Business Rule Validation (on Mutations)

| Operation | Validation |
|-----------|------------|
| `create(series_key)` | `series_id` not already exists |
| `add_book(series_id, book_identity)` | Series exists; book not already member; Series not ARCHIVED |
| `update_name(series_id, new_name)` | Series exists; Series not ARCHIVED |
| `archive(series_id)` | Series exists |
| `set_book_status(series_id, volume_number, status)` | Valid state transition per BookStatus machine |

### 10.3 Fail-Closed Principle

- **Any validation failure → Exception**, no partial load, no fallback defaults
- Corrupted manifest file → `IntegrityError` → operation aborted
- No silent data corruption

---

## 11. Same-Name Series Behavior (D-09 Confirmed)

| Scenario | Behavior |
|----------|----------|
| User creates "Passion" → `series_id=A` | Creates Series A |
| User creates "Passion" again → `series_id=B` | Creates Series B (different ID) |
| Series A and B both have `series_name="Passion"` | **Allowed** — completely isolated |
| User adds Book 1 to Series A | Book 1 in Series A only |
| User adds Book 1 to Series B | Book 1 in Series B only (different `volume_number` context) |
| No automatic merge, no name-based lookup | **Explicit `series_id` required** for all operations |

---

## 12. Cross-Series Isolation Primitives (D-08 Confirmed)

**Identity Namespace Isolation (Contract for Downstream Batches):**

| Downstream Component | Isolation Contract |
|---------------------|-------------------|
| `SeriesMemoryStore` | `series_character_id = schar_{sha256(series_id\|korean)}` |
| `SeriesEntityRegistry` | `series_entity_id = sentity_{sha256(series_id\|source\|type)}` |
| `SeriesGlossary` | File: `series_glossary_{series_id}.json` |
| `SeriesKnowledge` | Novel tier keyed by `series_id` |
| `SeriesCheckpoint` | File: `series_checkpoint_{series_id}.json` |
| `EntityResolver` | Series registry checked FIRST (USER level) |
| `KnowledgeRuntime` | Novel tier per `series_id` |

**Batch 5.1 delivers:** The `series_id` primitive and Manifest authority.
**Downstream batches MUST enforce:** Namespace isolation using `series_id` prefix.

---

## 13. CSI-01 ~ CSI-10 Acceptance Tests (D-08 Confirmed)

> **Hard Gates:** All must PASS. Any failure → Batch 5.1 not accepted.

| Test ID | Description | Batch 5.1 Verification |
|---------|-------------|------------------------|
| **CSI-01** | Same Korean name in Series A vs B → different `series_character_id` | Verify `compute_series_character_id()` uses `series_id` prefix |
| **CSI-02** | Same entity name in Series A vs B → different `series_entity_id` | Verify `compute_series_entity_id()` uses `series_id` prefix |
| **CSI-03** | Series A glossary locked term ≠ Series B | Verify file naming `series_glossary_{series_id}.json` |
| **CSI-04** | In-memory isolation: load Series A, then Series B | Verify `SeriesRegistry` returns independent manifests |
| **CSI-05** | Series A promotion doesn't leak to Series B | Verify `series_id` gating in all registry operations |
| **CSI-06** | Series A checkpoint restore doesn't load Series B | Verify checkpoint file naming `series_checkpoint_{series_id}.json` |
| **CSI-07** | Duplicate series_name → creates new Series, no merge | Verify `SeriesRegistry.create()` allows duplicate name, different ID |
| **CSI-08** | Delete Series A directory → Series B unaffected | Verify no cross-directory references |
| **CSI-09** | Concurrent Runtime instances with different Series | Verify `SeriesIdentity` passed explicitly, no global state |
| **CSI-10** | Series A archived → Series B active | Verify lifecycle state per-Series, no global lock |

**Test Location:** `tests/series/test_batch5_1_cross_series_isolation.py`

---

## 14. Frozen Contracts Audit

**Batch 5.1 MUST NOT modify (verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | ✅ No touch |
| Context Pipeline Contract | ✅ No touch |
| Prompt Pipeline Contract | ✅ No touch |
| Plugin Contract | ✅ No touch |
| Production Pipeline Contract | ✅ No touch |
| Translation Runtime Contract | ✅ No touch |
| Intelligence Contract | ✅ No touch |
| Knowledge Contract | ✅ No touch |
| Snapshot Contract | ✅ No touch |
| BookIntakeProcessor / Canonical Intake | ✅ No touch |
| Character Memory v2 core | ✅ No touch |
| Context/Scene Memory core | ✅ No touch |
| Entity Resolver core | ✅ No touch |
| KnowledgeRuntime core | ✅ No touch |
| Runtime Checkpoint core | ✅ No touch |

**New Contract Created by Batch 5.1:**
- **Series Identity Contract** (`core/series_identity/`) — to be added to Foundation Manifest in Batch 5.9

---

## 15. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| Any existing `core/character_memory_v2/` | ✅ No touch |
| Any existing `core/context_scene_memory/` | ✅ No touch |
| Any existing `core/entity_resolver/` | ✅ No touch |
| Any existing `core/knowledge_runtime/` | ✅ No touch |
| Any existing `core/book_intake/` | ✅ No touch |
| Any existing `core/translation_runtime/` | ✅ No touch |
| Any existing `core/translation_pipeline/` | ✅ No touch |
| Any existing `core/production_runtime/` | ✅ No touch |
| Any existing `core/runtime_checkpoint/` | ✅ No touch |
| Any Frozen Contract (9 existing) | ✅ No touch |
| Feature flag changes | ✅ No touch |
| TXT/EPUB/Translation behavior | ✅ No touch |
| Provider/Network/Translation execution | ✅ No touch |

---

## 16. Test Requirements

### 16.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_compute_series_id_deterministic` | Same canonical key → same ID |
| `test_compute_series_id_canonicalization` | Whitespace/case normalized |
| `test_series_identity_immutability` | `series_id` cannot change |
| `test_series_name_mutability` | `series_name` can change, ID stable |
| `test_manifest_roundtrip` | Save → load → fingerprint matches |
| `test_manifest_fingerprint_integrity` | Tampered file → IntegrityError |
| `test_book_ordering_sequential` | volume_number = max + 1 |
| `test_book_ordering_immutable` | Cannot reorder/insert gaps |
| `test_duplicate_book_rejected` | Same book_identity → error |
| `test_duplicate_name_allowed` | Same series_name → different series_id |
| `test_lifecycle_transitions` | Valid transitions only |
| `test_lifecycle_invalid_blocked` | Invalid transitions → error |
| `test_cross_series_isolation_identity` | Series A ID ≠ Series B ID for same name |
| `test_cross_series_isolation_manifest` | Manifests independent |
| `test_corrupted_manifest_fail_closed` | Bad hash → exception |
| `test_schema_validation` | Invalid schema → error |

### 16.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_id_deterministic_property` | 1000 |
| `test_manifest_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |

### 16.3 Cross-Series Isolation Tests (CSI-01 ~ CSI-10)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_01_series_character_id_isolation` | CSI-01 |
| `test_csi_02_series_entity_id_isolation` | CSI-02 |
| `test_csi_03_glossary_file_isolation` | CSI-03 |
| `test_csi_04_registry_inmemory_isolation` | CSI-04 |
| `test_csi_05_promotion_non_leakage` | CSI-05 |
| `test_csi_06_checkpoint_isolation` | CSI-06 |
| `test_csi_07_duplicate_name_no_merge` | CSI-07 |
| `test_csi_08_filesystem_isolation` | CSI-08 |
| `test_csi_09_runtime_concurrent_isolation` | CSI-09 |
| `test_csi_10_lifecycle_isolation` | CSI-10 |

---

## 17. Validation Gates

**All must PASS before Batch 5.1 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-01 ~ CSI-10 tests PASS
- [ ] No regression in existing 888 pytest tests
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 18. Git Scope Rules

**Allowed Changes:**
- **NEW** `core/series_identity/` (complete module)
- **NEW** `tests/series/test_batch5_1_*.py` (test files)
- **NEW** `docs/governance/rm8/series_identity_contract.md` (contract doc)

**Forbidden:**
- Any modification to existing production code
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 19. Delivery Rules

**Deliverables (working tree changes only, no staging):**
1. `core/series_identity/` module
2. `tests/series/test_batch5_1_*.py`
3. `docs/governance/rm8/series_identity_contract.md`
4. Updated `P0_STAGE5_FORMAL_SPECIFICATION.md` (if any spec clarifications needed)
5. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 20. Rollback Boundary

**Clean Rollback:** Delete `core/series_identity/` directory and `tests/series/test_batch5_1_*.py`.

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules

---

## 21. Provider / Network / Translation Policy

- **ZERO** provider calls
- **ZERO** network requests
- **ZERO** translation executions
- Pure offline deterministic computation only

---

## 22. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/series_identity/` — implementation
- `tests/series/` — tests
- `docs/governance/rm8/` — docs/contracts
- `artifacts/` — diagnostic output only

---

## 23. Completion Criteria

**Batch 5.1 Complete When:**

1. All §16 unit tests PASS
2. All §16 property-based tests PASS (1000 iterations)
3. All §13 CSI-01 ~ CSI-10 tests PASS
4. Validation gates (§17) all PASS
5. Git status shows only allowed new files
6. No production code modified
7. No Frozen Contracts modified

**Status Report:** "P0 Stage 5 Batch 5.1 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 24. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | D-01 ~ D-10 reflected, data models complete | 2026-08-18 |
| Owner | Authorization to proceed | ____________ |
| QA | CSI-01~10 test matrix accepted | ____________ |

---

*End of Batch 5.1 Implementation Task. Implementation NOT STARTED. Awaiting Owner Authorization.*

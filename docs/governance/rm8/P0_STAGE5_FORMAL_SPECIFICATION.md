# P0 Stage 5 — Series Continuity Formal Specification

**Baseline Commit:** `4b7b8781bae035466dc215ca0a265052f0055cda` (P0 Stage 4 Final Delivery)
**Specification Version:** 1.0
**Status:** Formal Specification — Owner Decisions Confirmed (D-01 ~ D-10)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_SERIES_CONTINUITY_PREFLIGHT_AUDIT.md`
**Amendment:** `docs/governance/rm8/P0_STAGE5_SPECIFICATION_AMENDMENT.md`

---

## 0. Governance Constraints (Non-Negotiable)

| Constraint | Requirement |
|------------|-------------|
| **A. No Redesign Character Memory v2** | Existing `MemoryRecord`, `MemoryStore`, `add_or_merge_memory`, evidence ranking, conflict resolution, expiry policies — **frozen** |
| **B. No Redesign Context/Scene Memory** | Existing `ContextMemoryRecord`, `SceneMemoryRecord`, `ContextMemoryStore`, `ExpiryKind` (SCENE_SCOPE, CHAPTER_SCOPE, NEVER) — **frozen** |
| **C. Additive Series Scope Extension Only** | New `series_*` modules; existing book-scoped modules unchanged |
| **D. No Archive of Existing Implementation** | All `core/character_memory_v2/`, `core/context_scene_memory/`, `core/entity_resolver/`, `core/knowledge_runtime/` remain active |
| **E. No Production Feature Flags** | No activation of series features without Owner sign-off |
| **F. No Real Provider/Network/Translation Execution** | Specification only; all validation offline |
| **G. No Unauthorized Architecture Decisions** | All decisions marked `OWNER_APPROVAL_REQUIRED` require explicit Owner authorization |
| **H. Frozen Contracts Immutable** | Foundation Manifest contracts (runtime, context, prompt, plugin, production, translation, intelligence, knowledge, snapshot) — **cannot be modified** |
| **I. Series vs Book/Chapter/Scene Fact Separation** | Canonical (NEVER) vs Local (SCENE/CHAPTER/SESSION) — explicit boundary |
| **J. Hydration/Promotion Unidirectional Boundary** | Series→Book hydration (read-only for book); Book→Series promotion (approval-gated) |
| **K. Cross-Series Namespace Isolation** | `series_character_id` = `sha256(series_id\|korean_name)`; no collision across series |
| **L. Single-Book Workflow Full Compatibility** | Existing TXT/EPUB workflows unchanged; series layer optional additive |

---

## 1. Series Identity

### 1.1 Series ID (D-01 Confirmed)

```python
def compute_series_id(user_defined_series_key: str) -> str:
    """
    Deterministic series identity from user-provided stable series key.

    The series key is canonicalized (trimmed, lowercased) before hashing.
    """
    canonical_key = user_defined_series_key.strip().lower()
    return hashlib.sha256(f"series|{canonical_key}".encode("utf-8")).hexdigest()[:16]
```

**Properties (D-01, D-02 Confirmed):**
- User-provided stable series key → deterministic `series_id`
- `series_id` is **immutable** after creation (D-01)
- `series_name` (display name) is **mutable** and separate from `series_id` (D-02)
- Stable across sessions, machines, NTPE versions
- Not derived from file paths (unlike `book_identity`)

### 1.2 Series Identity Model

```python
@dataclass(frozen=True)
class SeriesIdentity:
    series_id: str          # Immutable, from compute_series_id()
    series_name: str        # Mutable display name
    created_at: str         # ISO timestamp
    updated_at: str         # ISO timestamp, updated on name change
```

### 1.2 Series Manifest (D-03, D-09 Confirmed)

**File:** `series_manifest_{series_id}.json` (stored in `output/series/{series_id}/`)

```json
{
  "schema_name": "ntpe.series_manifest",
  "schema_version": "1.0",
  "series_id": "a1b2c3d4e5f6g7h8",
  "series_name": "Passion",
  "lifecycle_status": "ACTIVE",
  "created_at": "2026-08-18T00:00:00Z",
  "updated_at": "2026-08-18T00:00:00Z",
  "books": [
    {
      "volume_number": 1,
      "book_identity": "b1o2k3i4d5e6n7t8",
      "source_path": "input/Passion_v01.txt",
      "title": "Passion 第1卷",
      "status": "completed",
      "completed_at": "2026-08-15T12:00:00Z",
      "content_fingerprint": "sha256...",
      "manifest_fingerprint": "sha256..."
    },
    {
      "volume_number": 2,
      "book_identity": "b2o3k4i5d6e7n8t9",
      "source_path": "input/Passion_v02.txt",
      "title": "Passion 第2卷",
      "status": "in_progress",
      "content_fingerprint": "sha256...",
      "manifest_fingerprint": "sha256..."
    }
  ],
  "series_memory_hash": "sha256_of_series_memory_store",
  "series_checkpoint_hash": "sha256_of_latest_series_checkpoint",
  "manifest_fingerprint": "sha256_of_above_payload"
}
```

**Authority & Mutability Rules (D-03 Confirmed):**

| Field | Authority | Mutability | Rule |
|-------|-----------|------------|------|
| `series_id` | Creation | **IMMUTABLE** | Never changes |
| `series_name` | User | **MUTABLE** | Rename allowed, ID unchanged (D-02) |
| `lifecycle_status` | System | **STATE_MACHINE** | CREATED → ACTIVE → COMPLETED → ARCHIVED (D-04) |
| `created_at` | System | **IMMUTABLE** | Creation timestamp |
| `updated_at` | System | **AUTO** | Updated on any manifest change |
| `books[].volume_number` | System | **IMMUTABLE** | Sequential 1-based, no gaps, no reorder |
| `books[].book_identity` | Book Intake | **IMMUTABLE** | References existing Stage 4 Book ID (D-10) |
| `books[].source_path` | User/System | **IMMUTABLE** | Original path at add-time, never updated |
| `books[].title` | User | **MUTABLE** | Display title editable |
| `books[].status` | Workflow | **STATE_MACHINE** | pending → in_progress → completed → promoted → archived |
| `books[].content_fingerprint` | File | **IMMUTABLE** | SHA256 of source file content |
| `books[].manifest_fingerprint` | Book Intake | **IMMUTABLE** | BookIntakeManifest fingerprint |
| `series_memory_hash` | System | **DERIVED** | Updated after Promotion |
| `series_checkpoint_hash` | System | **DERIVED** | Updated after SeriesCheckpoint creation |
| `manifest_fingerprint` | System | **DERIVED** | SHA256 of canonical manifest payload |

**Book Membership & Ordering Rules (D-03, D-09 Confirmed):**
- Manifest is **append-only** for books; existing entries immutable
- `volume_number` assigned sequentially at add-time: `max(existing) + 1`
- **Same-name Series ≠ Same Series** (D-09): Two Series with identical `series_name` but different `series_id` are completely isolated — no shared manifest, memory, entity registry, knowledge, or state
- User must **explicitly select** existing `series_id` to continue a Series; no auto-merge by name
- Duplicate `book_identity` in same Series → rejected (one book per Series)

**Derived/Runtime State (Never Written Back to Manifest Authority):**
- `series_memory_hash`, `series_checkpoint_hash`, `manifest_fingerprint` are system-derived
- Book runtime state (`in_progress`, chunk progress) not in Manifest
- No reverse write from derived state to authority fields

---

## 2. Series Lifecycle (D-04 Confirmed)

### 2.1 Series Lifecycle

```
Series Lifecycle:
    ┌─────────────┐
    │  CREATED    │  ← SeriesRegistry.create(series_key)
    └──────┬──────┘
           │ add_book (first)
           ▼
    ┌─────────────┐
    │  ACTIVE     │  ← At least 1 book in_progress or completed
    ├─────────────┤
    │ books: [    │
    │   {vol:1,   │
    │    status:  │
    │   in_prog}  │
    │ ]           │
    └──────┬──────┘
           │ all books promoted, no in_progress
           ▼
    ┌─────────────┐
    │  COMPLETED  │  ← All books promoted, no in_progress
    └──────┬──────┘
           │ User archives / long-term inactive
           ▼
    ┌─────────────┐
    │  ARCHIVED   │  ← Read-only, no new books accepted
    └─────────────┘
```

**State Transitions (D-04 Confirmed):**

| From → To | Trigger | Actor |
|-----------|---------|-------|
| CREATED → ACTIVE | First book added | User |
| ACTIVE → COMPLETED | All books promoted, no in_progress | System (auto) |
| ACTIVE → ARCHIVED | User explicit archive | User |
| COMPLETED → ARCHIVED | User explicit archive | User |

### 2.2 Book Lifecycle (Within Series Manifest)

```
pending → in_progress → completed → promoted → archived
                ↘ failed
```

- Batch 5.1 **does not implement** full Book runtime lifecycle
- Book status in Manifest tracks membership state only
- Full translation lifecycle handled in later batches

---

## 3. Series / Book / Chapter / Chunk Hierarchy

```
Series (series_id)
  └── SeriesManifest (ordering, metadata)
  └── SeriesMemoryStore (canonical NEVER-expiry facts)
  └── SeriesEntityRegistry (USER overrides, canonical entities)
  └── SeriesGlossary (canonical locked terms)
  └── SeriesKnowledge (Novel level in KnowledgeMerger hierarchy)
  └── SeriesCheckpoint (series-level recovery point)
       │
       ├── Book 1 (book_identity, volume_number=1)
       │     ├── BookManifest (from book_intake)
       │     ├── BookMemoryStore (Character Memory v2 - hydrated from Series)
       │     ├── BookContextStore (Context/Scene Memory - book-local)
       │     ├── BookEntityMap (resolved from SeriesEntityRegistry + runtime)
       │     ├── BookGlossary (SeriesGlossary + book-local additions)
       │     ├── BookKnowledge (Volume level in KnowledgeMerger)
       │     └── BookCheckpoint
       │          │
       │          ├── Session A (session_id)
       │          │     ├── SessionState
       │          │     ├── SessionCheckpoint
       │          │     │
       │          │     ├── Chunk 1 (chunk_index=0)
       │          │     ├── Chunk 2 (chunk_index=1)
       │          │     └── ...
       │          │
       │          └── Session B (resume)
       │
       ├── Book 2 (book_identity, volume_number=2)
       │     └── (same structure)
       │
       └── Book N...
```

**Scope Definitions:**

| Scope | Lifetime | Memory Types | Expiry |
|-------|----------|--------------|--------|
| **Series** | Cross-book, cross-session | Canonical names, relationships, fixed translations, USER overrides, world facts | NEVER |
| **Book** | Single book translation | Derived/canonical names, book-local entities, glossary additions, scene state | NEVER (canonical) / CHAPTER/SCENE (local) |
| **Chapter** | Single chapter | Scene summaries, chapter-local context | CHAPTER_SCOPE |
| **Scene** | Single scene | Location, time, participants, speaker, events | SCENE_SCOPE |
| **Chunk** | Single translation unit | Previous translation excerpt, immediate context | SEGMENT_SCOPE |
| **Session** | Single NTPE run | Active scene, progress, ephemeral overrides | SESSION_SCOPE |

---

## 3. Series Memory Store

### 3.1 New Module: `core/series_memory/`

```
core/series_memory/
├── __init__.py
├── models.py              # SeriesCharacterRecord, SeriesEntityRecord, SeriesFactRecord
├── store.py               # SeriesMemoryStore (canonical facts only)
├── persistence.py         # Load/save series_memory_{series_id}.json
├── migration.py           # BookMemoryStore → SeriesMemoryStore promotion
├── hydration.py           # SeriesMemoryStore → BookMemoryStore hydration
└── validation.py          # Series memory validation
```

### 3.2 SeriesCharacterRecord (Canonical Only)

```python
@dataclass(frozen=True)
class SeriesCharacterRecord:
    """Canonical character fact — NEVER expires, series-scoped."""
    series_character_id: str        # sha256(series_id|korean_name)[:16]
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
- No `expiry_policy` — always `NEVER`

### 3.3 SeriesMemoryStore Operations

| Operation | Description |
|-----------|-------------|
| `get_canonical_name(series_character_id)` | Returns approved canonical name |
| `get_relationships(series_character_id)` | Returns all APPROVED relationships |
| `get_all_canonical_facts()` | Returns all SeriesCharacterRecord |
| `hydrate_book_store(book_store, book_identity)` | Copies relevant canonical facts to BookMemoryStore |
| `promote_from_book(book_store, book_identity, approval_gate)` | Promotes APPROVED facts from book to series (see §10) |

---

## 4. Character Memory v2 — Series Scope Extension

### 4.1 No Changes to Existing Models/Store

**FROZEN:** `core/character_memory_v2/models.py`, `store.py`, `lifecycle.py`, `selection.py`, `validation.py`

### 4.2 Extension: BookMemoryStore Hydration

```python
# In core/character_memory_v2/hydration.py (NEW)
def hydrate_from_series(
    book_store: MemoryStore,
    series_store: SeriesMemoryStore,
    book_identity: str,
    series_id: str,
    korean_to_series_id: dict[str, str]  # korean_name -> series_character_id
) -> HydrationReport:
    """
    Copy Series canonical facts into BookMemoryStore as APPROVED records.

    Rules:
    - Only APPROVED SeriesCharacterRecord copied
    - BookMemoryStore records created with:
        - character_id = book-scoped hash (existing behavior)
        - approval_status = APPROVED
        - approval_metadata.reviewer = "series_hydration"
        - approval_metadata.decision_reference = f"series:{series_id}"
        - supersedes_memory_id = None (fresh book record)
    - Existing book records with same fact_key:
        - If book record is PENDING → superseded by series canonical
        - If book record is APPROVED with different value → CONFLICT (requires resolution)
        - If book record matches series → DUPLICATE (no action)
    """
```

### 4.3 BookMemoryStore Promotion to Series

See §10 (Book → Series Promotion Rules).

---

## 5. Context/Scene Memory — Series Scope Extension

### 5.1 No Changes to Existing Models/Store

**FROZEN:** `core/context_scene_memory/models.py`, `store.py`, `lifecycle.py`, `scene_state.py`, `context_selection.py`

### 5.2 Design Principle: Context is Book-Local

**Context/Scene Memory does NOT have Series scope.** By design:

| Context Type | Scope | Cross-Book? |
|--------------|-------|-------------|
| Scene state (location, time, participants) | Scene | ❌ Never |
| Chapter summary | Chapter | ❌ Never |
| Previous translation excerpt | Chunk/Scene | ❌ Never |
| Speaker state | Scene | ❌ Never |
| Event state | Scene | ❌ Never |
| Unresolved references | Scene/Chapter | ❌ Never |
| Terminology state | Book (via Glossary) | ✅ Via SeriesGlossary |

**Rationale:** Scene context is inherently book-local. A new book starts new scenes.

### 5.3 Series Glossary Integration

SeriesGlossary (§7) provides canonical terminology to BookContextStore via hydration.

---

## 6. Series Entity Registry

### 6.1 New Module: `core/series_entity_registry/`

```
core/series_entity_registry/
├── __init__.py
├── models.py              # SeriesEntityRecord
├── registry.py            # SeriesEntityRegistry
├── persistence.py         # Load/save series_entities_{series_id}.json
└── integration.py         # Integration with EntityResolver
```

### 6.2 SeriesEntityRecord

```python
@dataclass(frozen=True)
class SeriesEntityRecord:
    series_entity_id: str       # sha256(series_id|source_name|entity_type)[:16]
    source_name: str            # Korean source (e.g., "정태의")
    canonical_target: str       # Approved Chinese (e.g., "鄭泰義")
    entity_type: EntityType     # CHARACTER, PLACE, TERMINOLOGY, ORGANIZATION
    source_level: InjectionSource  # Always USER for series registry
    metadata: dict              # provenance, book_coverage, etc.
    approved_at: str
    approved_by: str            # "user" or "series_promotion"
    version: int
```

### 6.3 EntityResolver Integration

```python
# In core/entity_resolver/resolver.py (EXTENSION - additive)
class EntityResolver:
    def __init__(self, ..., series_registry: SeriesEntityRegistry | None = None):
        self.series_registry = series_registry
        # ... existing init ...

    def _resolve_single(self, extracted: ExtractedEntity) -> ResolvedEntity:
        # 1. USER override (existing)
        # 2. SERIES REGISTRY (NEW - higher than RUNTIME)
        if self.series_registry and extracted.source in self.series_registry:
            record = self.series_registry.get(extracted.source)
            return ResolvedEntity(
                source=extracted.source,
                target=record.canonical_target,
                entity_type=extracted.entity_type,
                source_level=InjectionSource.USER.value,  # Series = USER level
                metadata={"series_registry": True, "series_entity_id": record.series_entity_id}
            )
        # 3. RUNTIME (existing)
        # 4. LEARNING (existing)
        # 5. AUTO (existing)
```

**Precedence Update:** USER = SERIES > RUNTIME > LEARNING > AUTO
(Series registry acts as persistent USER override)

---

## 7. Series Glossary

### 7.1 Integration with Existing Glossary Builder

**No new module.** Extends `core/glossary_builder.py` behavior:

```python
# In core/glossary_builder.py (EXTENSION)
def build_series_glossary(series_id: str, series_manifest: SeriesManifest) -> SeriesGlossary:
    """
    Build canonical glossary from all completed books in series.

    Rules:
    - Only terms from books with status="completed"
    - Only terms with locked=True or confidence >= 0.95
    - Merged across all volumes (existing merge_glossary logic)
    - Output: series_glossary_{series_id}.json
    """
```

### 7.2 SeriesGlossary Structure

```json
{
  "schema_name": "ntpe.series_glossary",
  "schema_version": "1.0",
  "series_id": "...",
  "terms": {
    "정태의": {
      "translation": "鄭泰義",
      "category": "person_name",
      "locked": true,
      "source_books": ["book_id_1", "book_id_2"],
      "confidence": 1.0,
      "approved_at": "2026-08-18T00:00:00Z"
    }
  },
  "glossary_hash": "sha256..."
}
```

---

## 8. series_character_id Namespace Isolation

### 8.1 Identity Computation

```python
def compute_series_character_id(series_id: str, korean_name: str) -> str:
    """Namespace-isolated character ID."""
    return f"schar_{hashlib.sha256(f'{series_id}|{korean_name}'.encode()).hexdigest()[:16]}"

def compute_book_character_id(book_identity: str, korean_name: str) -> str:
    """Book-local character ID (existing behavior, unchanged)."""
    return f"char_{hashlib.sha256(korean_name.encode()).hexdigest()[:16]}"
```

### 8.2 Isolation Guarantees

| Scenario | series_character_id | book_character_id | Collision? |
|----------|---------------------|-------------------|------------|
| Series A: "李某", Series B: "李某" | `schar_{A|李某}` ≠ `schar_{B|李某}` | Same `char_{李某}` | **NO** (series isolated) |
| Same series, Book 1 & Book 2: "李某" | Same `schar_{series|李某}` | Different `char_{李某}` | **NO** (series canonical) |
| Same book, two "李某" characters | Same `schar_{series|李某}` | Same `char_{李某}` | Requires disambiguation (existing) |

### 8.3 Mapping Table

SeriesMemoryStore maintains:
```python
korean_to_series_id: dict[str, str]  # "李某" -> "schar_..."
series_id_to_book_ids: dict[str, set[str]]  # "schar_..." -> {"book_id_1", "book_id_2"}
```

---

## 9. Series → Book Hydration

### 9.1 Hydration Trigger

- At Book translation start (when `load_or_create_character_memory` called)
- At Book Context/Scene Memory initialization
- At EntityResolver initialization for book

### 9.2 Hydration Data Flow

```
SeriesMemoryStore (canonical NEVER facts)
    │
    ├── Character canonical names → BookMemoryStore (as APPROVED records)
    ├── SeriesEntityRegistry → EntityResolver (as USER-level overrides)
    ├── SeriesGlossary → BookGlossary / BookContextStore (as locked terms)
    └── SeriesKnowledge (Novel level) → KnowledgeMerger (populates Novel tier)
```

### 9.3 Hydration Rules

| Source | Target | Transformation |
|--------|--------|----------------|
| SeriesCharacterRecord.canonical_name | BookMemoryRecord (FactType.CANONICAL_NAME) | New record, APPROVED, reviewer="series_hydration" |
| SeriesCharacterRecord aliases | BookMemoryRecord (FactType.NAME_VARIANT) | New records, APPROVED |
| SeriesCharacterRecord relationships | BookMemoryRecord (FactType.RELATIONSHIP) | New records, APPROVED |
| SeriesEntityRecord | EntityResolver.user_overrides | Direct injection (USER level) |
| SeriesGlossary terms | GlossaryBuilder override / BookContextStore | Locked terms, status="series_canonical" |
| SeriesKnowledge (Novel) | KnowledgeMerger.set_novel() | Populates Novel tier in hierarchy |

### 9.4 Hydration Idempotency

- Hydration is **idempotent** — re-running produces same BookMemoryStore state
- Uses `series_memory_hash` in SeriesManifest to detect changes
- BookMemoryStore tracks `hydration_source = f"series:{series_id}:{series_memory_hash}"`

---

## 10. Book → Series Promotion Rules

### 10.1 Promotion Boundary (CRITICAL)

**Series owns canonical facts. Book proposes. Promotion requires approval.**

```
Book Translation
    │
    ├── BookMemoryStore accumulates facts (PENDING → APPROVED via user review)
    ├── Book completes (all chunks translated, user review done)
    │
    └── Promotion Gate (MANUAL or AUTO with policy)
         │
         ├── For each APPROVED BookMemoryRecord:
         │     If fact_type in {CANONICAL_NAME, RELATIONSHIP, TERMINOLOGY_PREFERENCE}:
         │         If series has no record → PROMOTE (create SeriesCharacterRecord)
         │         If series has record with SAME value → NO-OP
         │         If series has record with DIFFERENT value → CONFLICT (requires MANUAL resolution)
         │
         └── For EntityResolver user_overrides created during book:
               If series_registry has no entry → PROMOTE (create SeriesEntityRecord)
               If series_registry has SAME target → NO-OP
               If series_registry has DIFFERENT target → CONFLICT (MANUAL)
```

### 10.2 Promotion Policy (Configurable)

```python
@dataclass(frozen=True)
class PromotionPolicy:
    auto_promote_canonical_names: bool = False      # Requires MANUAL by default
    auto_promote_relationships: bool = False
    auto_promote_terminology: bool = False
    auto_promote_entities: bool = False
    conflict_resolution: str = "manual"             # "manual" | "book_wins" | "series_wins"
    require_user_approval: bool = True
```

**Default:** All `False`, `conflict_resolution="manual"`, `require_user_approval=True`

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

## 11. Series Checkpoint Hierarchy

### 11.1 New Module: `core/series_checkpoint/`

```
core/series_checkpoint/
├── __init__.py
├── models.py              # SeriesCheckpoint, BookCheckpointRef, SessionCheckpointRef
├── manager.py             # SeriesCheckpointManager
├── persistence.py         # Load/save series_checkpoint_{series_id}.json
└── recovery.py            # Recovery orchestration
```

### 11.2 SeriesCheckpoint Model

```python
@dataclass(frozen=True)
class SeriesCheckpoint:
    series_id: str
    checkpoint_id: str                    # sha256(series_id|timestamp)[:12]
    created_at: str
    series_memory_hash: str               # Hash of SeriesMemoryStore
    series_entity_registry_hash: str      # Hash of SeriesEntityRegistry
    series_glossary_hash: str             # Hash of SeriesGlossary
    series_knowledge_hash: str            # Hash of SeriesKnowledge (Novel level)
    book_checkpoints: tuple[BookCheckpointRef, ...]
    manifest_fingerprint: str             # Hash of SeriesManifest
    state_hash: str                       # Hash of all above

@dataclass(frozen=True)
class BookCheckpointRef:
    book_identity: str
    volume_number: int
    book_memory_hash: str
    book_context_hash: str
    latest_session_checkpoint_id: str | None
    status: str                           # "in_progress" | "completed" | "promoted"

@dataclass(frozen=True)
class SessionCheckpointRef:
    session_id: str
    chunk_index: int
    progress: ProgressState
    context_memory_hash: str
    request_manifest: RequestManifest | None
```

### 11.3 Checkpoint Creation Triggers

| Event | Checkpoint Level |
|-------|------------------|
| Book translation starts | BookCheckpointRef created in SeriesCheckpoint |
| Book chunk completed | SessionCheckpoint updated; BookCheckpointRef updated |
| Book completed + promotion done | SeriesCheckpoint created (new series_memory_hash) |
| Session resume | SessionCheckpoint loaded |
| Series-level manual save | SeriesCheckpoint created |

---

## 12. Resume / Restore Behavior

### 12.1 Series-Level Resume

```python
def resume_series(series_id: str) -> SeriesResumeReport:
    """
    1. Load SeriesManifest
    2. Load latest SeriesCheckpoint
    3. Validate all hashes (memory, entity, glossary, knowledge, manifest)
    4. Restore SeriesMemoryStore, SeriesEntityRegistry, SeriesGlossary
    5. For each BookCheckpointRef with status="in_progress":
         - Resume book from latest SessionCheckpoint
    6. Return resume report with next actions
    """
```

### 12.2 Book-Level Resume (Within Series)

```python
def resume_book_in_series(series_id: str, book_identity: str) -> BookResumeReport:
    """
    1. Load SeriesManifest → get book volume_number
    2. Load SeriesCheckpoint → get BookCheckpointRef
    3. Hydrate BookMemoryStore from SeriesMemoryStore
    4. Load BookContextStore (book-local)
    5. Load latest SessionCheckpoint → restore chunk_index, progress
    6. Restore EntityResolver with SeriesEntityRegistry + book runtime
    7. Return resume report
    """
```

### 12.3 Fresh Book in Existing Series

```python
def start_new_book_in_series(
    series_id: str,
    book_identity: str,
    volume_number: int,
    source_path: Path
) -> BookStartReport:
    """
    1. Validate series_id exists in SeriesManifest
    2. Validate volume_number = max(existing) + 1
    3. Create BookManifest (book_intake)
    4. Create fresh BookMemoryStore, hydrate from SeriesMemoryStore
    5. Create fresh BookContextStore
    6. Initialize EntityResolver with SeriesEntityRegistry
    7. Add BookCheckpointRef to SeriesManifest (status="pending")
    8. Return BookStartReport with hydration summary
    """
```

---

## 13. Cross-Series Contamination Prevention

### 13.1 Namespace Isolation (Enforced at All Layers)

| Layer | Isolation Mechanism |
|-------|---------------------|
| SeriesMemoryStore | `series_character_id = schar_{sha256(series_id|korean)}` |
| SeriesEntityRegistry | `series_entity_id = sentity_{sha256(series_id|source|type)}` |
| SeriesGlossary | File per series: `series_glossary_{series_id}.json` |
| SeriesCheckpoint | File per series: `series_checkpoint_{series_id}.json` |
| BookMemoryStore (hydrated) | Book records carry `series_id` provenance; `series_character_id` reference |
| EntityResolver | Series registry checked FIRST (USER level); book runtime SECOND |
| KnowledgeRuntime | Novel tier keyed by `series_id` |

### 13.2 Validation Rules

```python
def validate_cross_series_isolation(series_id: str) -> ValidationReport:
    """
    - No SeriesMemoryStore record has series_id != target series_id
    - No SeriesEntityRegistry entry has series_id != target series_id
    - No BookMemoryStore record from hydration has mismatched series_id
    - No EntityResolver resolution returns series entity from different series
    """
```

### 13.3 Same-Name Character Handling

| Scenario | Handling |
|----------|----------|
| Series A: "李某" (protagonist), Series B: "李某" (villain) | Different `series_character_id`; completely isolated |
| User translates Series A Book 1, then Series B Book 1 | Separate SeriesManifest, separate hydration, no leakage |
| User opens both series in same NTPE session | Each book translation loads its own series_id context |

---

## 14. Multiple Books in Same Series

### 14.1 Book Ordering

- `volume_number` assigned sequentially at book addition (1, 2, 3...)
- Immutable once assigned
- SeriesManifest enforces: `volume_number[n] = volume_number[n-1] + 1`

### 14.2 Concurrent Books

**Not supported in Stage 5.** One book translation at a time per series.

### 14.3 Book Status Transitions

```
pending → in_progress → completed → promoted → archived
                    ↘ failed
```

- `promoted` = Book→Series promotion completed
- Only `completed` books contribute to SeriesMemoryStore/SeriesGlossary

---

## 15. Book Addition Workflow

### 15.1 User Flow (CLI/Launcher)

```bash
# 1. Create/Select Series
ntpe series create "Passion"           # Creates series_id, SeriesManifest

# 2. Add Book 1
ntpe series add-book "Passion" input/Passion_v01.txt

# 3. Translate Book 1
ntpe translate --series "Passion" --book 1

# 4. Review & Promote Book 1
ntpe series promote-book "Passion" --book 1

# 5. Add Book 2
ntpe series add-book "Passion" input/Passion_v02.txt

# 6. Translate Book 2 (auto-hydrated from Series)
ntpe translate --series "Passion" --book 2
```

### 15.2 Programmatic API

```python
# Series creation
series = SeriesRegistry.create("Passion")  # Returns SeriesManifest

# Book addition
book_ref = series.add_book(source_path="input/Passion_v01.txt")  # Returns BookCheckpointRef

# Translation (hydrated)
runtime = TranslationRuntime(series_id=series.series_id, book_identity=book_ref.book_identity)
runtime.translate()

# Promotion (after user review)
series.promote_book(book_ref.book_identity, policy=PromotionPolicy(...))
```

---

## 16. Existing Single-Book TXT Workflow Compatibility

### 16.1 No Changes to TXT Pipeline

- `core/translation_runtime/runtime.py` → `translate_txt()` unchanged
- `lts/txt_translation_runtime.py` unchanged
- `core/translation_pipeline/` unchanged

### 16.2 Series as Optional Context

```python
# In TranslationRuntime (EXTENSION - additive)
def translate_txt(self, options, series_id: str | None = None, book_identity: str | None = None):
    if series_id and book_identity:
        # Series-aware translation: hydrate from series
        series_context = SeriesOrchestrator.hydrate_book(series_id, book_identity)
        options.series_context = series_context
    # ... existing TXT translation logic unchanged
```

### 16.3 Backward Compatibility Guarantees

| Existing Behavior | Preserved? |
|-------------------|------------|
| `ntpe_production_translate.py` CLI | ✅ Yes |
| `ntpe_launcher.py` dry-run/validate | ✅ Yes |
| TXT resume from `.ntpe_runtime_checkpoints` | ✅ Yes |
| Batch translation | ✅ Yes |
| No series_id provided → no hydration | ✅ Yes |

---

## 17. Existing EPUB Workflow Compatibility

### 17.1 Book Intake Unchanged

- `core/book_intake/` pipeline unchanged
- `BookIntakeManifest` unchanged
- EPUB → TXT extraction unchanged

### 17.2 Series Integration Point

After `BookIntakeProcessor` produces `BookIntakeResult`:
```python
# In EPUB workflow (EXTENSION)
if series_id:
    series = SeriesRegistry.get(series_id)
    book_ref = series.add_book_from_intake(intake_result)
    # Continue with series-aware translation
```

---

## 18. Character Memory v2 Migration Compatibility

### 18.1 Existing Migration Path Preserved

`core/character_memory_v2/persistence.py`:
- `migrate_lts_to_v2()` → unchanged
- `load_or_create_character_memory()` → unchanged (adds optional `series_id` parameter)

### 18.2 Series-Aware Migration

```python
def load_or_create_character_memory(
    *,
    output_dir: Path,
    input_path: Path,
    project_name: str,
    lts_path: Path | None = None,
    series_id: str | None = None,        # NEW
    book_identity: str | None = None,    # NEW (pre-computed)
) -> tuple[MemoryStore, dict]:
    """
    If series_id provided:
    1. Try load existing book memory (existing behavior)
    2. Try LTS migration (existing behavior)
    3. Create fresh MemoryStore
    4. If series_id: HYDRATE from SeriesMemoryStore
    """
```

---

## 19. Existing Context/Scene Memory Compatibility

### 19.1 No Changes to Persistence

`core/context_scene_memory/persistence.py` unchanged.

### 19.2 Series-Aware Initialization

```python
def load_or_create_context_memory(
    *,
    output_dir: Path,
    input_path: Path,
    project_name: str,
    series_id: str | None = None,        # NEW
    book_identity: str | None = None,    # NEW
) -> tuple[ContextMemoryStore, dict]:
    """
    If series_id provided:
    1. Load existing or create fresh (existing behavior)
    2. Hydrate SeriesGlossary terms as locked CONTEXT_TYPE.TERMINOLOGY_STATE
    """
```

---

## 20. Existing Entity Resolver Compatibility

### 20.1 No Breaking Changes

`core/entity_resolver/resolver.py`:
- New optional `series_registry` parameter
- Default `None` → existing behavior unchanged
- Precedence: SERIES (USER) > RUNTIME > LEARNING > AUTO

### 20.2 Extractor Integration

```python
# In core/entity_resolver/extractor.py (EXTENSION)
def build_known_entities_from_runtime(runtime, series_registry=None) -> dict:
    known = {}  # existing logic
    if series_registry:
        for entity in series_registry.get_all():
            known[entity.source_name] = entity.entity_type
    return known
```

---

## 21. Frozen Contracts

### 21.1 Existing Frozen Contracts (Immutable)

| Contract | Location | Status |
|----------|----------|--------|
| Runtime Contract | `core/translation_runtime/runtime_contract.py` | FROZEN |
| Context Pipeline Contract | Referenced in Foundation | FROZEN |
| Prompt Pipeline Contract | Referenced in Foundation | FROZEN |
| Plugin Contract | Referenced in Foundation | FROZEN |
| Production Pipeline Contract | Referenced in Foundation | FROZEN |
| Translation Runtime Contract | Referenced in Foundation | FROZEN |
| Intelligence Contract | Referenced in Foundation | FROZEN |
| Knowledge Contract | Referenced in Foundation | FROZEN |
| Snapshot Contract | Referenced in Foundation | FROZEN |

### 21.2 New Contracts Required (Stage 5 Deliverables)

| Contract | Module | Status |
|----------|--------|--------|
| Series Identity Contract | `core/series_identity/` | **NEW** |
| Series Memory Contract | `core/series_memory/` | **NEW** |
| Series Entity Contract | `core/series_entity_registry/` | **NEW** |
| Series Checkpoint Contract | `core/series_checkpoint/` | **NEW** |
| Series Orchestration Contract | `core/series_orchestration/` | **NEW** |

**Action:** Add to Foundation Manifest upon Stage 5 completion.

---

## 22. Forbidden Modifications

| Category | Forbidden |
|----------|-----------|
| **Core Memory Models** | `MemoryRecord`, `ContextMemoryRecord`, `SceneMemoryRecord`, `FactType`, `ContextType`, `Evidence`, `ApprovalStatus`, `MemoryStatus`, `RecordStatus`, `ExpiryKind` |
| **Core Store Logic** | `MemoryStore.add_or_merge_memory`, `ContextMemoryStore.add_or_merge_context`, conflict resolution, evidence ranking, deduplication |
| **Core Lifecycle** | `approve_memory`, `reject_memory`, `supersede_memory`, `expire_memory`, `rollback_memory`, context/scene equivalents |
| **Core Selection** | `select_prompt_eligible_memories`, `select_context_for_prompt` |
| **Entity Resolver Core** | `EntityResolver._resolve_single` precedence logic (only additive series_registry) |
| **Knowledge Runtime Core** | `KnowledgeMerger` hierarchy, `MergedRuntime`, `DOMAIN_STRATEGIES` |
| **Checkpoint Core** | `CheckpointSnapshot`, `ProgressState`, `RequestManifest`, `RuntimeCheckpointManager` |
| **Frozen Contracts** | Any modification to 9 existing frozen contracts |
| **Production Code** | Any `core/translation_runtime/`, `core/translation_pipeline/`, `core/book_intake/`, `core/production_runtime/` behavioral changes |

---

## 23. Security / Fail-Closed Requirements

### 23.1 Fail-Closed Principles

| Operation | Fail-Closed Behavior |
|-----------|---------------------|
| SeriesManifest load | Invalid schema/hash → exception, no partial load |
| SeriesMemoryStore load | Corrupted file → exception, no fallback to empty |
| Hydration | Hash mismatch → exception, translation blocked |
| Promotion | Conflict detected → exception, manual resolution required |
| Checkpoint restore | Integrity failure → exception, no silent corruption |
| Cross-series access | Wrong series_id → exception, no data leakage |

### 23.2 Deterministic Hashes

All persistence files include:
- `state_hash` / `file_hash` / `manifest_fingerprint` / `checkpoint_hash`
- Computed via `_canonical_json` + SHA256
- Verified on every load

### 23.3 No Secrets in Series Artifacts

- SeriesManifest, SeriesMemoryStore, SeriesCheckpoint contain **no API keys, credentials, PII**
- Only translation metadata, canonical facts, hashes

---

## 24. Deterministic Identity Requirements

### 24.1 Identity Computation (All Deterministic)

| Identity | Computation | Inputs |
|----------|-------------|--------|
| `series_id` | `sha256("series|{user_name}")[:16]` | User-defined series name |
| `book_identity` | `sha256("{project}|{resolved_path}")[:16]` | Project name + file path |
| `series_character_id` | `sha256("{series_id}|{korean_name}")[:16]` | Series ID + Korean name |
| `series_entity_id` | `sha256("{series_id}|{source}|{type}")[:16]` | Series ID + source + type |
| `content_fingerprint` | `sha256(text.encode("utf-8"))` | Source text |
| `manifest_fingerprint` | `sha256(canonical_json(payload))` | Manifest payload |

### 24.2 Reproducibility Guarantee

Same inputs → Same identities → Same hashes → Bit-for-bit identical artifacts across machines/runs.

---

## 25. Artifact Isolation

### 25.1 Directory Structure

```
output/
├── series/
│   └── {series_id}/
│       ├── series_manifest_{series_id}.json
│       ├── series_memory_{series_id}.json
│       ├── series_entities_{series_id}.json
│       ├── series_glossary_{series_id}.json
│       ├── series_knowledge_{series_id}.json
│       └── series_checkpoint_{series_id}.json
├── books/
│   └── {book_identity}/
│       ├── character_memory_{book_identity}.json
│       ├── context_scene_memory_{book_identity}.json
│       ├── book_manifest_{book_identity}.json
│       └── checkpoints/
│           └── {session_id}/
│               └── session_checkpoint.json
└── translations/
    └── {book_identity}/
        └── translated_chunks/
```

### 25.2 Isolation Rules

- Series artifacts **never** in book directories
- Book artifacts **never** in series directories
- No symlinks or cross-references via filesystem
- All cross-references via explicit identity fields in JSON

---

## 26. Test Strategy

### 26.1 Unit Tests (Per Module)

| Module | Test Focus |
|--------|------------|
| `series_identity` | ID computation, manifest validation, book ordering |
| `series_memory` | Canonical record CRUD, hydration, promotion, conflict detection |
| `series_entity_registry` | Registry CRUD, EntityResolver integration, precedence |
| `series_checkpoint` | Hierarchy creation, hash validation, recovery |
| `series_orchestration` | Book addition, translation start, promotion workflow |

### 26.2 Integration Tests

| Scenario | Test |
|----------|------|
| Series creation → Book 1 add → Translate → Promote → Book 2 add → Translate | Full workflow |
| Cross-series isolation: Series A "李某" vs Series B "李某" | No contamination |
| Resume: Close NTPE mid-Book 2 → Reopen → Resume | Checkpoint recovery |
| Fresh book in existing series: Book 3 without Book 1-2 context | Hydration only |
| Backward compat: TXT translation without series_id | No regression |

### 26.3 Property-Based Tests

- Deterministic identity: Same inputs → same outputs (1000 iterations)
- Hash integrity: Load → save → load → hash matches
- Promotion idempotency: Promote same book twice → no duplicate series records

---

## 27. Acceptance Gates

### 27.1 Per-Batch Gates

| Batch | Gate |
|-------|------|
| 5.1 Series Identity | `ntpe_validate.py PASS`, compileall PASS, manifest round-trip test PASS |
| 5.2 Series Memory | Unit tests PASS, hydration round-trip PASS, promotion conflict detection PASS |
| 5.3 Series Entity Registry | EntityResolver integration test PASS, precedence test PASS |
| 5.4 Series Glossary | GlossaryBuilder integration PASS, cross-volume merge PASS |
| 5.5 Series Knowledge | KnowledgeMerger Novel tier populated PASS, resolver queries PASS |
| 5.6 Series Checkpoint | 4-level hierarchy save/load PASS, recovery test PASS |
| 5.7 Orchestration | Full Passion 6-book scenario PASS, UX flow validated |
| 5.8 Migration | LTS → v2 → Series migration PASS, backward compat PASS |
| 5.9 Validation Freeze | All contracts frozen, `ntpe_validate.py` updated, docs complete |

### 27.2 Stage 5 Final Acceptance

- [ ] All 9 batches PASS
- [ ] `ntpe_validate.py` ALL PASS (0 warnings)
- [ ] `python -m compileall core/` 0 errors
- [ ] `git diff --check` clean
- [ ] Passion 6-book scenario: Book 1→6 continuous translation with continuity
- [ ] Cross-series contamination test: 0 leaks
- [ ] Single-book TXT/EPUB workflow: 0 regressions
- [ ] All new contracts added to Foundation Manifest
- [ ] Documentation complete

---

## 28. Batch Decomposition

| Batch | Name | Scope | Duration Estimate |
|-------|------|-------|-------------------|
| **5.1** | Series Identity & Manifest | `core/series_identity/` — ID, Manifest, Registry, Persistence | 1 week |
| **5.2** | Series Memory Store | `core/series_memory/` — Canonical records, Store, Hydration, Promotion | 2 weeks |
| **5.3** | Series Entity Registry | `core/series_entity_registry/` — Registry, EntityResolver integration | 1 week |
| **5.4** | Series Glossary | `core/glossary_builder.py` extensions — SeriesGlossary, merge | 1 week |
| **5.5** | Series Knowledge Population | `core/knowledge_runtime/` — Novel/Volume tier population | 1 week |
| **5.6** | Series Checkpoint Hierarchy | `core/series_checkpoint/` — 4-level checkpoint, recovery | 1 week |
| **5.7** | Series Orchestration | `core/series_orchestration/` — Coordinator, workflow, UX integration | 2 weeks |
| **5.8** | Migration & Compatibility | All migration paths, backward compat, regression tests | 1 week |
| **5.9** | Validation & Freeze | Contract freeze, `ntpe_validate` update, docs, final acceptance | 1 week |

**Total Estimated:** 11 weeks

---

## 29. Architecture Decisions — CONFIRMED (D-01 ~ D-10)

All architecture decisions previously requiring Owner approval have been **confirmed**:

| Decision | Confirmed Choice | Reference |
|----------|------------------|-----------|
| **Series ID Source** | User-provided stable series key (canonicalized) | D-01 |
| **Series ID Mutability** | Immutable; display name (`series_name`) mutable | D-02 |
| **Manifest Authority** | Explicit authority boundary; derived state never overwrites | D-03 |
| **Series Lifecycle** | CREATED → ACTIVE → COMPLETED → ARCHIVED | D-04 |
| **Artifact Layout** | `output/series/{series_id}/` and `output/books/{book_identity}/` | D-05 |
| **Series/Book Ownership** | Series = canonical/NEVER; Book = local/scoped; Hydration read-only; Promotion controlled | D-06 |
| **Promotion Default** | MANUAL for all fact types | D-07 |
| **Cross-Series Isolation** | CSI-01 ~ CSI-10 as hard acceptance gates | D-08 |
| **Same-Name Series** | No auto-merge; explicit series_id selection required | D-09 |
| **Book ID Semantics** | Stage 4 frozen definition unchanged | D-10 |

---

## 30. Specification Summary

This specification defines **additive Series scope extension** to NTPE's existing book-scoped architecture:

1. **Series Identity** — `series_id` from user name, `SeriesManifest` with ordered books
2. **Series Memory Store** — Canonical NEVER-expiry facts (`SeriesCharacterRecord`), namespace-isolated via `series_character_id`
3. **Hydration** — Series→Book at translation start (read-only for book)
4. **Promotion** — Book→Series at book completion (approval-gated, conflict-aware)
5. **Entity Registry** — Persistent USER-level overrides per series
6. **Glossary/Knowledge** — Series-canonical terms populate Novel/Volume tiers
7. **Checkpoint** — 4-level hierarchy (Series/Book/Session/Chunk) with hash integrity
8. **Isolation** — Cross-series contamination prevented by namespace prefixing
9. **Compatibility** — Existing TXT/EPUB/LTS workflows unchanged; series layer optional

**No redesign of Character Memory v2, Context/Scene Memory, Entity Resolver core, Knowledge Runtime core, or Checkpoint core.**

---

## 31. Next Step — Batch 5.1 Authorization

**All Owner decisions confirmed (D-01 ~ D-10).**

**Status:** **P0 Stage 5 Batch 5.1 — Series Identity & Manifest — READY FOR AUTHORIZATION**

Upon Owner authorization → Proceed to Batch 5.1 Implementation.

---

*End of Formal Specification. No production code modified. Owner decisions confirmed. Awaiting Batch 5.1 authorization.*

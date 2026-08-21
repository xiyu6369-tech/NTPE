# P0 Stage 5 Batch 5.7 — Series Orchestration Preflight Audit

**Baseline Commit:** `0bfa97d` (HEAD = origin/main, Batch 5.6 delivered)
**Audit Date:** 2026-08-22
**Status:** Preflight Audit — No Production Code Modified

---

## 1. Executive Summary

This audit examines NTPE's current architecture to establish the preflight analysis for **P0 Stage 5 Batch 5.7 — Series Orchestration**. The baseline includes all completed Stage 5 batches:

- **Batch 5.1** (Series Identity & Manifest): `core/series_identity/` — `SeriesIdentity`, `SeriesManifest`, `SeriesRegistry`, deterministic `series_id`, derived hashes
- **Batch 5.2** (Series Memory Store): `core/series_memory/` — `SeriesMemoryStore`, `SeriesCharacterRecord`, hydration (Series→Book), promotion (Book→Series MANUAL gate), persistence
- **Batch 5.3** (Series Entity Registry): `core/series_entity_registry/` — `SeriesEntityRecord`, `SeriesEntityRegistry`, EntityResolver integration with SERIES precedence (USER level), persistence
- **Batch 5.4** (Series Glossary): `core/glossary_builder.py` extensions — `SeriesGlossary`, `build_series_glossary()`, `load_series_glossary()`, `merge_into_series_glossary()`, persistence
- **Batch 5.5** (Series Knowledge Population): `core/knowledge_runtime/loader.py`, `manager.py` extensions — `SeriesKnowledge`, Novel/Volume tier population, persistence
- **Batch 5.6** (Series Checkpoint Hierarchy): `core/series_checkpoint/` — `SeriesCheckpoint`, `BookCheckpointRef`, `SessionCheckpointRef`, `SeriesCheckpointManager`, 4-level hierarchy, recovery orchestration, persistence

**Primary Finding:** NTPE has **all foundational Series infrastructure** implemented and validated, but **no orchestration layer** that:
- Coordinates multi-book workflow (create series, add book, translate, promote)
- Provides CLI/UX commands for series operations
- Integrates series context into TranslationRuntime
- Manages the complete Passion 6-book scenario end-to-end

**Batch 5.7 must establish:**
- `SeriesTranslationCoordinator` — High-level orchestration for series workflows
- Multi-book workflow state machine (pending → in_progress → completed → promoted)
- CLI integration (`ntpe series create`, `ntpe series add-book`, `ntpe series promote-book`, `ntpe translate --series`)
- `TranslationRuntime` series context injection (optional `series_id`, `book_identity` parameters)
- Cross-series isolation enforcement at orchestration level
- CSI-05 hard gate validation for all operations

---

## 2. Existing Capability Inventory

### 2.1 Series Identity (Batch 5.1) — `core/series_identity/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesIdentity** | Complete | Immutable `series_id`, mutable `series_name`, `created_at`, `updated_at` |
| **SeriesManifest** | Complete | Books with volume_number, status, derived hashes (memory, checkpoint, entity, glossary, knowledge) |
| **SeriesRegistry** | Complete | `create()`, `get()`, `list_all()`, `add_book()`, `update_name()`, `set_book_status()`, `archive()`, all hash update methods |
| **Persistence** | Complete | `output/series/{series_id}/series_manifest_{series_id}.json` with atomic writes |
| **Validation** | Complete | Schema validation, fingerprint verification, fail-closed |
| **Derived Hash Fields** | Complete | All 5 derived hashes defined, `update_series_checkpoint_hash()` implemented |

### 2.2 Series Memory Store (Batch 5.2) — `core/series_memory/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesMemoryStore** | Complete | Canonical NEVER-expiry facts only, namespace-isolated `series_character_id` |
| **SeriesCharacterRecord** | Complete | Canonical names, relationships, terminology preferences, APPROVED only |
| **Hydration** | Complete | Series→Book (READ-ONLY), idempotent, conflict detection (PENDING→APPROVED upgrade, CONFLICT on different values) |
| **Promotion** | Complete | Book→Series with MANUAL approval gate (D-07 frozen), conflict detection |
| **Persistence** | Complete | `output/series/{series_id}/series_memory_{series_id}.json` |
| **Mapping** | Complete | `korean_to_series_id`, `series_id_to_book_ids` |

### 2.3 Series Entity Registry (Batch 5.3) — `core/series_entity_registry/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesEntityRegistry** | Complete | `series_entity_id = sentity_{sha256(series_id|source|type)[:16]}`, typed queries required |
| **EntityResolver Integration** | Complete | SERIES precedence (USER level) > RUNTIME > LEARNING > AUTO via `user_overrides` |
| **Hydration** | Complete | READ-ONLY projection to `EntityResolver.user_overrides` dict |
| **Promotion** | Complete | Book→Series with MANUAL gate, USER_OVERRIDE source_level only |
| **Persistence** | Complete | `output/series/{series_id}/series_entities_{series_id}.json` |
| **Conflict Resolution** | Complete | Manual resolution: book_wins / series_wins / manual |

### 2.4 Series Glossary (Batch 5.4) — `core/glossary_builder.py`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesGlossary** | Complete | Canonical terms from completed books, locked/high-confidence only |
| **build_series_glossary()** | Complete | Merges completed book glossaries, enriches with EntityRegistry + CharacterMemory |
| **merge_into_series_glossary()** | Complete | Promotion with MANUAL gate, conflict detection |
| **Persistence** | Complete | `output/series/{series_id}/series_glossary_{series_id}.json` |
| **Integration** | Complete | `get_locked_dictionary()` for frozen components, `get_alias_map()` |

### 2.5 Series Knowledge Population (Batch 5.5) — `core/knowledge_runtime/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesKnowledge** | Complete | Novel tier population from SeriesMemoryStore + SeriesGlossary |
| **load_series_knowledge()** | Complete | Populates KnowledgeMerger Novel tier (character + glossary) |
| **populate_volume_tier()** | Complete | Book-specific facts at Volume tier (KEY_OVERRIDE) |
| **Persistence** | Complete | `output/series/{series_id}/series_knowledge_{series_id}.json` |
| **Manifest Integration** | Complete | `update_series_knowledge_hash()` called after population |

### 2.6 Series Checkpoint Hierarchy (Batch 5.6) — `core/series_checkpoint/`

| Component | Status | Details |
|-----------|--------|---------|
| **SeriesCheckpoint** | Complete | 4-level hierarchy: Series → Book → Session → Chunk with hash integrity |
| **SeriesCheckpointManager** | Complete | Creation, persistence, validation, manifest integration |
| **Recovery** | Complete | `resume_series()`, `resume_book_in_series()`, `start_new_book_in_series()` |
| **Persistence** | Complete | `output/series/{series_id}/series_checkpoint_{series_id}.json` |
| **Frozen Integration** | Complete | References existing `runtime_checkpoint`, `production_runtime`, `translation_session` checkpoints by ID/hash |

### 2.7 Translation Runtime (Existing) — `core/translation_runtime/`

| Component | Status | Details |
|-----------|--------|---------|
| **TranslationRuntime** | Complete | Facade for TXT/batch/package translation, provider integration, sessions, pipelines |
| **translate_txt()** | Complete | Delegates to `lts.txt_translation_runtime.translate_txt()` (frozen LTS) |
| **translate_batch()** | Complete | Delegates to `lts.batch_translation_runtime.translate_batch()` (frozen LTS) |
| **translate_package()** | Complete | Provider-based package translation |
| **Extension Points** | Available | `translate_txt()`, `translate_package()` accept optional parameters |

### 2.8 Launcher (Existing) — `ntpe_launcher.py`

| Component | Status | Details |
|-----------|--------|---------|
| **ntpe_launcher.py** | Complete | Dry-run, validate-config, list providers/models/languages, GUI launch |
| **Commands** | Limited | No series commands currently |

---

## 3. Current Architecture — Gap Analysis

| Capability | Current State | Required for Batch 5.7 |
|------------|---------------|------------------------|
| **Series Orchestration Coordinator** | **NONE** | `SeriesTranslationCoordinator` for multi-book workflow |
| **Series Workflow State Machine** | **NONE** | Book lifecycle: pending → in_progress → completed → promoted |
| **CLI Series Commands** | **NONE** | `ntpe series create`, `add-book`, `promote-book`, `list`, `status` |
| **TranslationRuntime Series Context** | **NONE** | Optional `series_id`, `book_identity` in `translate_txt()`, `translate_package()` |
| **Launcher Series Integration** | **NONE** | Series commands in ntpe_launcher.py |
| **Passion 6-Book Scenario** | **NONE** | End-to-end test: Book 1→6 continuous with continuity |
| **Cross-Series Isolation at Orchestration** | **NONE** | Hard enforcement in coordinator, CLI, runtime |
| **Backward Compatibility** | **PARTIAL** | TXT/EPUB without series_id must work identically |

---

## 4. Series Orchestration Boundary Definition

### 4.1 Series-Level Authority (What Belongs to Orchestration)

| Authority | Description | Source |
|-----------|-------------|--------|
| **Series Workflow** | Create series, add books, translate books, promote books | New `SeriesTranslationCoordinator` |
| **Book Lifecycle** | Status transitions in SeriesManifest | Orchestrator calls `SeriesRegistry.set_book_status()` |
| **Translation Coordination** | Hydrate from series, translate, promote to series | New `runtime_integration.py` |
| **CLI/UX** | User-facing commands for series operations | New `cli_integration.py`, `ntpe_launcher.py` extension |
| **Cross-Series Validation** | Enforce isolation at every operation | CSI-05 hard gates |

### 4.2 Book-Local Scope (What Remains Book-Local)

| Scope | Description | Storage |
|-------|-------------|---------|
| **Book Translation** | Actual chunk-by-chunk translation | Existing `TranslationRuntime` / LTS |
| **Book Memory/Context** | Character Memory v2, Context/Scene Memory | Existing per-book persistence |
| **Session/Chunk Checkpoints** | Progress, cursor, context state | Existing `runtime_checkpoint` (frozen) |
| **Production Checkpoints** | Job/segment state | Existing `production_runtime` (frozen) |

### 4.3 Orchestration Data Flow

```
SeriesTranslationCoordinator (Orchestrator)
    ├── SeriesRegistry (SeriesManifest authority)
    ├── SeriesMemoryStore (Canonical facts)
    ├── SeriesEntityRegistry (Canonical entities)
    ├── SeriesGlossary (Canonical terms)
    ├── SeriesKnowledge (Novel tier)
    ├── SeriesCheckpointManager (Recovery)
    │
    ├── TranslationRuntime (Execution - additive series context)
    │   ├── translate_txt(series_id, book_identity) → hydrates before translate
    │   └── translate_package(series_id, book_identity) → hydrates before translate
    │
    ├── BookIntake (Book identity, manifest)
    │
    └── CLI Integration (User commands)
        ├── series create "Name"
        ├── series add-book "Name" file.txt
        ├── series promote-book "Name" --book 1
        ├── translate --series "Name" --book 1
        └── series status "Name"
```

---

## 5. Series Orchestration Identity Design

### 5.1 Namespace Isolation (Extended)

| Layer | Mechanism |
|-------|-----------|
| **File Path** | All series artifacts under `output/series/{series_id}/` |
| **Manifest Key** | All operations require explicit `series_id` |
| **CLI Commands** | Series name resolved to `series_id` via Registry |
| **Translation Context** | `series_id` + `book_identity` passed to runtime |
| **Checkpoint** | Series checkpoint includes all book/session refs |
| **Recovery** | `series_id` required for all resume operations |

### 5.2 CLI Command Design

```bash
# Series Management
ntpe series create "Passion"                          # Creates series_id, SeriesManifest
ntpe series list                                       # Lists all series
ntpe series status "Passion"                          # Shows series manifest + progress
ntpe series rename "Passion" "New Name"               # Updates series_name (series_id unchanged)

# Book Management
ntpe series add-book "Passion" input/Passion_v01.txt  # Adds BookRef, volume_number=1
ntpe series add-book "Passion" input/Passion_v02.txt  # Adds BookRef, volume_number=2

# Translation
ntpe translate --series "Passion" --book 1            # Translates Book 1 with series hydration
ntpe translate --series "Passion" --book 2            # Translates Book 2 with series hydration

# Promotion
ntpe series promote-book "Passion" --book 1           # Promotes Book 1 facts to series (MANUAL gate)

# Recovery
ntpe series resume "Passion"                          # Resume from latest SeriesCheckpoint
ntpe series resume "Passion" --book 2                 # Resume specific book in series
```

---

## 6. Cross-Series Isolation — Hard Failure Analysis

| Case | Current Behavior | Required Behavior | Failure Mode |
|------|------------------|-------------------|--------------|
| Series A translate, Series B context leak | N/A (no series context) | Hydration only from matching series_id | **HARD FAIL** if cross-series data used |
| CLI add-book to wrong series | N/A | SeriesManifest validates book membership | **HARD FAIL** if book not in manifest |
| TranslationRuntime series_id mismatch | N/A (no series_id param) | Runtime validates series_id matches book | **HARD FAIL** on mismatch |
| Checkpoint recovery wrong series | N/A | `resume_series()` validates series_id | **HARD FAIL** on mismatch |
| Book promotion to wrong series | N/A | `promote_book()` validates series_id | **HARD FAIL** on mismatch |
| Manifest hash mismatch | N/A | `series_checkpoint_hash` validates integrity | **HARD FAIL** on fingerprint mismatch |

**All cases MUST be hard failures.** No silent fallback, no auto-merge.

---

## 7. Series Orchestration Data Models

### 7.1 SeriesTranslationCoordinator (in `coordinator.py`)

```python
class SeriesTranslationCoordinator:
    """High-level orchestration for series translation workflows."""

    def __init__(
        self,
        output_root: Path,
        series_registry: SeriesRegistry,
        series_memory_store: SeriesMemoryStore,
        series_entity_registry: SeriesEntityRegistry,
        series_glossary: SeriesGlossary,
        series_knowledge: SeriesKnowledge,
        series_checkpoint_manager: SeriesCheckpointManager,
        translation_runtime: TranslationRuntime,
    ): ...

    def create_series(self, user_defined_series_key: str, series_name: str | None = None) -> SeriesCreateResult:
        """Create new series. Returns SeriesManifest."""

    def add_book(
        self,
        series_id: str,
        source_path: Path,
        title: str | None = None,
    ) -> BookAddResult:
        """Add book to series. Returns BookRef with volume_number."""

    def translate_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        dry_run: bool = False,
        options: Any | None = None,
    ) -> TranslationReport:
        """Translate a specific book in series with series context hydration."""

    def promote_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        approval_gate: bool = True,
    ) -> PromotionReport:
        """Promote completed book facts to series (MANUAL gate)."""

    def get_series_status(self, series_id: str) -> SeriesStatusReport:
        """Get current series status: books, progress, next actions."""

    def resume_series(self, series_id: str) -> SeriesResumeReport:
        """Resume entire series from checkpoint."""

    def resume_book(self, series_id: str, volume_number: int) -> BookResumeReport:
        """Resume specific book in series."""
```

### 7.2 Workflow State Machine (in `workflow.py`)

```python
@dataclass(frozen=True)
class BookWorkflowState:
    volume_number: int
    book_identity: str
    status: str  # "pending" | "in_progress" | "completed" | "promoted" | "failed" | "archived"
    hydration_done: bool
    translation_started_at: str | None
    translation_completed_at: str | None
    promotion_completed_at: str | None
    current_chunk: int
    total_chunks: int
    last_error: str | None

@dataclass(frozen=True)
class SeriesWorkflowState:
    series_id: str
    series_name: str
    lifecycle_status: str  # "CREATED" | "ACTIVE" | "COMPLETED" | "ARCHIVED"
    books: tuple[BookWorkflowState, ...]
    next_volume_number: int
    next_actions: list[str]  # e.g., ["translate:volume_2", "promote:volume_1"]
```

### 7.3 Runtime Integration Models (in `runtime_integration.py`)

```python
@dataclass(frozen=True)
class SeriesContext:
    """Series context injected into TranslationRuntime."""
    series_id: str
    book_identity: str
    volume_number: int
    series_memory_hash: str
    series_entity_registry_hash: str
    series_glossary_hash: str
    series_knowledge_hash: str
    book_memory_hash: str
    book_context_hash: str
    session_checkpoint_id: str | None

def build_series_context(
    series_id: str,
    book_identity: str,
    output_root: Path,
    series_registry: SeriesRegistry,
    series_memory_store: SeriesMemoryStore,
    series_entity_registry: SeriesEntityRegistry,
    series_glossary: SeriesGlossary,
    series_knowledge: SeriesKnowledge,
    series_checkpoint_manager: SeriesCheckpointManager,
) -> SeriesContext:
    """Build series context for translation runtime."""

def inject_series_context(
    runtime: TranslationRuntime,
    series_context: SeriesContext,
) -> None:
    """Inject series context into runtime (hydration, resolver, glossary, knowledge)."""
```

---

## 8. TranslationRuntime Integration

### 8.1 Additive Changes to `core/translation_runtime/runtime.py`

```python
# EXTENSION - Add optional series context parameters
def translate_txt(
    self,
    options: Any,
    series_id: str | None = None,
    book_identity: str | None = None,
) -> dict[str, Any]:
    if series_id and book_identity:
        # Series-aware translation: hydrate from series
        series_context = SeriesOrchestrator.build_series_context(series_id, book_identity, ...)
        SeriesOrchestrator.inject_series_context(self, series_context)
    # ... existing TXT translation logic unchanged

def translate_package(
    self,
    package: dict,
    package_path: str | Path | None = None,
    series_id: str | None = None,
    book_identity: str | None = None,
) -> dict[str, Any]:
    if series_id and book_identity:
        # Series-aware translation
        series_context = SeriesOrchestrator.build_series_context(series_id, book_identity, ...)
        SeriesOrchestrator.inject_series_context(self, series_context)
    # ... existing package translation logic unchanged
```

### 8.2 Hydration Sequence

```
translate_txt(series_id, book_identity)
    → build_series_context()
        → Load SeriesManifest, SeriesCheckpoint
        → Hydrate BookMemoryStore from SeriesMemoryStore
        → Load BookContextStore (book-local)
        → Initialize EntityResolver with SeriesEntityRegistry.user_overrides
        → Initialize KnowledgeMerger with Novel tier (SeriesKnowledge) + Volume tier (Book)
        → Initialize Glossary with SeriesGlossary locked terms
    → inject_series_context() into runtime
    → Execute existing translation logic (unchanged)
```

---

## 9. Manifest Integration

### 9.1 SeriesManifest Authority Boundary (Per D-03)

| Manifest Field | Authority | Orchestration Relationship |
|----------------|-----------|----------------------------|
| `series_id` | Manifest (IMMUTABLE) | Orchestrator keyed by this |
| `series_name` | Manifest (MUTABLE) | Orchestrator references for display |
| `books[]` | Manifest (APPEND-ONLY) | Orchestrator adds books, updates status |
| `series_memory_hash` | Derived (SeriesMemoryStore) | Independent, mirrored in checkpoint |
| `series_entity_registry_hash` | Derived (SeriesEntityRegistry) | Independent, mirrored in checkpoint |
| `series_glossary_hash` | Derived (SeriesGlossary) | Independent, mirrored in checkpoint |
| `series_knowledge_hash` | Derived (SeriesKnowledge) | Independent, mirrored in checkpoint |
| `series_checkpoint_hash` | Derived (SeriesCheckpoint) | Populated by Batch 5.6 |
| `manifest_fingerprint` | Derived (System) | SHA256 of canonical manifest payload |

### 9.2 Orchestration Responsibility

After each orchestration operation, Manifest is updated via existing Registry methods:

```python
# After add_book
series_registry.add_book(...)  # Updates manifest, increments volume_number

# After set_book_status (in_progress, completed, promoted)
series_registry.set_book_status(series_id, volume_number, new_status)

# After promote_book
series_memory_store.promote_from_book(...)  # Updates series memory
series_memory_hash = series_memory_store.series_memory_hash
series_registry.update_series_memory_hash(series_id, series_memory_hash)

# After glossary promotion
series_glossary = merge_into_series_glossary(...)
glossary_hash = series_glossary.glossary_hash
series_registry.update_series_glossary_hash(series_id, glossary_hash)

# After knowledge population
knowledge_population_report = knowledge_runtime_manager.load_series_knowledge(...)
knowledge_hash = knowledge_population_report.knowledge_hash
series_registry.update_series_knowledge_hash(series_id, knowledge_hash)

# After checkpoint creation
checkpoint_manager.create_checkpoint(series_id)
# → Already calls update_series_checkpoint_hash() internally
```

---

## 10. Persistence Design

### 10.1 No New Persistence Files

Batch 5.7 **does not create new persistence formats**. It uses existing:

| Artifact | Location | Owner |
|----------|----------|-------|
| SeriesManifest | `output/series/{series_id}/series_manifest_{series_id}.json` | Batch 5.1 |
| SeriesMemoryStore | `output/series/{series_id}/series_memory_{series_id}.json` | Batch 5.2 |
| SeriesEntityRegistry | `output/series/{series_id}/series_entities_{series_id}.json` | Batch 5.3 |
| SeriesGlossary | `output/series/{series_id}/series_glossary_{series_id}.json` | Batch 5.4 |
| SeriesKnowledge | `output/series/{series_id}/series_knowledge_{series_id}.json` | Batch 5.5 |
| SeriesCheckpoint | `output/series/{series_id}/series_checkpoint_{series_id}.json` | Batch 5.6 |
| Book Memory | `output/books/{book_identity}/character_memory_{book_identity}.json` | Existing |
| Book Context | `output/books/{book_identity}/context_scene_memory_{book_identity}.json` | Existing |

---

## 11. Acceptance Test Matrix for Batch 5.7

| Test ID | Category | Description | Expected Result | Failure Condition |
|---------|----------|-------------|-----------------|-------------------|
| **SO-01** | Series Create | `ntpe series create "Passion"` → SeriesManifest | Manifest created, series_id valid | Missing manifest or invalid ID |
| **SO-02** | Add Book | `ntpe series add-book "Passion" file.txt` → BookRef | Book added, volume_number=1 | Book not added or wrong volume |
| **SO-03** | Translate with Series | `ntpe translate --series "Passion" --book 1` → hydrated | BookMemoryStore has series facts | No hydration or wrong series data |
| **SO-04** | Promote Book | `ntpe series promote-book "Passion" --book 1` → SeriesMemoryStore updated | Canonical facts in SeriesMemoryStore | Promotion fails or wrong facts |
| **SO-05** | Full Passion 6-Book | Book 1→6 continuous with continuity | All books translated, continuity maintained | Any book lacks continuity |
| **SO-06** | Cross-Series Contamination | Series A "李某" ≠ Series B "李某" | Separate series_id, no leakage | Cross-series data access |
| **SO-07** | Backward Compat TXT | TXT translation without series_id works identically | Same output as baseline | Regression in TXT workflow |
| **SO-08** | Backward Compat EPUB | EPUB workflow without series_id works identically | Same output as baseline | Regression in EPUB workflow |
| **SO-09** | Series Resume | `ntpe series resume "Passion"` → restores all levels | All stores restored, books resumable | Hash mismatch or incomplete restore |
| **SO-10** | Book Resume | `ntpe series resume "Passion" --book 2` | Book hydrated, session restored | Hydration fails or session missing |
| **SO-11** | Provider/Network/Translation | Run all Batch 5.7 tests | 0/0/0 execution | Any external call |
| **SO-12** | Root Hygiene | Check repo root after test run | No new files in root | Files created in root |
| **SO-13** | Frozen Contract Isolation | No modification to frozen modules | Existing tests PASS | Frozen files modified |
| **SO-14** | CLI Integration | All series commands work via ntpe_launcher | Commands execute, output valid | Command fails or wrong output |

---

## 12. Dependencies Summary

| Dependency | Type | Notes |
|------------|------|-------|
| `core.series_identity` | Required | SeriesRegistry, SeriesManifest, SeriesIdentity |
| `core.series_memory` | Required | SeriesMemoryStore, hydration, promotion |
| `core.series_entity_registry` | Required | SeriesEntityRegistry, resolver integration |
| `core.glossary_builder` | Required | SeriesGlossary, build/merge/promotion |
| `core.knowledge_runtime` | Required | SeriesKnowledge, Novel/Volume tier |
| `core.series_checkpoint` | Required | SeriesCheckpointManager, recovery |
| `core.translation_runtime` | Required | TranslationRuntime (additive series context) |
| `core.book_intake` | Required | Book identity, BookIntakeManifest |
| `core.character_memory_v2` | Required | BookMemoryStore, load_or_create_character_memory |
| `core.context_scene_memory` | Required | BookContextStore |
| `ntpe_launcher.py` | Additive | Series CLI commands |

**No dependencies on:** `core.translation_pipeline`, `core.production_runtime` (except checkpoint ref), `core.runtime_orchestrator`, `lts/`

---

## 13. Frozen Contracts Audit

**Batch 5.7 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | No touch |
| Context Pipeline Contract | No touch |
| Prompt Pipeline Contract | No touch |
| Plugin Contract | No touch |
| Production Pipeline Contract | No touch |
| Translation Runtime Contract | No touch (additive params only) |
| Intelligence Contract | No touch |
| Knowledge Contract | No touch |
| Snapshot Contract | No touch |
| Character Memory v2 core | No touch |
| Context/Scene Memory core | No touch |
| Entity Resolver core | No touch (uses existing user_overrides) |
| Runtime Checkpoint core | No touch |
| Production Runtime Checkpoint | No touch |
| Translation Session Checkpoint | No touch |
| All 9 Foundation Frozen Contracts | No touch |

**New Contract Created by Batch 5.7:**
- **Series Orchestration Contract** (`core/series_orchestration/`) — to be added to Foundation Manifest in Batch 5.9

---

## 14. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/translation_runtime/runtime.py` core TXT/batch logic | **FROZEN** (only additive optional params) |
| `core/translation_pipeline/` | **FROZEN** |
| `core/book_intake/` | **FROZEN** |
| `core/production_runtime/` | **FROZEN** |
| `lts/` | **FROZEN** |
| `core/character_memory_v2/` models/store/lifecycle/selection/validation | **FROZEN** |
| `core/context_scene_memory/` models/store/lifecycle/scene_state/context_selection | **FROZEN** |
| `core/entity_resolver/` models/injector/_resolve_single core logic | **FROZEN** |
| `core/knowledge_runtime/` models/merger/snapshot/resolver | **FROZEN** |
| `core/runtime_checkpoint/` | **FROZEN** |
| Any Frozen Contract (9 existing) | **FROZEN** |
| Feature flag changes | **FROZEN** |
| TXT/EPUB/Translation behavior (without series_id) | **FROZEN** |
| Provider/Network/Translation execution | **FROZEN** |

---

## 15. Owner Decisions Required

| Decision | Options | Status |
|----------|---------|--------|
| **CLI Command Design** | Proposed in §5.2 | **NEEDS OWNER CONFIRMATION** |
| **Concurrent Books Policy** | Confirmed: DISALLOWED in Stage 5 (Spec §14.2) | FROZEN (D-10) |
| **TranslationRuntime Series Parameters** | Add optional `series_id`, `book_identity` to `translate_txt()`, `translate_package()` | **NEEDS OWNER CONFIRMATION** |
| **Launcher Integration** | Add series subcommands to ntpe_launcher.py | **NEEDS OWNER CONFIRMATION** |
| **Dry-Run Series Support** | Extend `--dry-run` for series workflows | **NEEDS OWNER CONFIRMATION** |
| **Passion 6-Book Test Data** | Need actual Passion 6-book test corpus | **NEEDS OWNER CONFIRMATION** |

---

## 16. Blockers

1. **Batch 5.6 must be accepted** (provides SeriesCheckpointManager, recovery orchestration)
2. **Owner decisions needed** for CLI design, TranslationRuntime parameters, launcher integration
3. **No technical blockers** — all infrastructure modules exist and are validated

---

## 17. Deliverables

1. `docs/governance/rm8/P0_STAGE5_BATCH5_7_PREFLIGHT_AUDIT.md` (this document)
2. `docs/governance/rm8/P0_STAGE5_BATCH5_7_IMPLEMENTATION_TASK.md` (implementation specification)

---

## 18. Validation Results (Preflight)

| Check | Result |
|-------|--------|
| `ntpe_validate.py` | PASS WITH WARNINGS (1 pre-existing warning: optional import) |
| `python -m compileall core/` | PASS (0 errors) |
| `git diff --check` | PASS (clean, only CRLF warnings on pre-existing files) |
| Provider Execution | 0 (audit only) |
| Network Calls | 0 (audit only) |
| Translation Execution | 0 (audit only) |
| Root Hygiene | PASS (no root files created by audit) |
| Production Code Modified | NO (audit only) |

---

## 19. Final Verdict

### Is NTPE Ready for Batch 5.7 Implementation?

> **BLOCKED — Owner Decisions Required**

### Blocking Reasons:

1. **CLI Command Design** — Owner must confirm command structure in §5.2
2. **TranslationRuntime Series Parameters** — Owner must confirm additive parameter approach
3. **Launcher Integration** — Owner must confirm ntpe_launcher.py extension approach
4. **Dry-Run Series Support** — Owner must confirm dry-run extension for series
5. **Passion 6-Book Test Data** — Owner must provide or confirm test corpus availability

### All Frozen Decisions (No Owner Action Needed):

| Decision | FROZEN Choice | Reference |
|----------|---------------|-----------|
| Series ID Source | User-provided stable series key | D-01 |
| Series ID Mutability | Immutable; display name mutable | D-02 |
| Manifest Authority | Explicit authority boundary | D-03 |
| Series Lifecycle | CREATED → ACTIVE → COMPLETED → ARCHIVED | D-04 |
| Artifact Layout | `output/series/{series_id}/` and `output/books/{book_identity}/` | D-05 |
| Series/Book Ownership | Series = canonical/NEVER; Book = local/scoped | D-06 |
| Promotion Default | MANUAL for all fact types | D-07 |
| Cross-Series Isolation | CSI-01 ~ CSI-10 as hard acceptance gates | D-08 |
| Same-Name Series | No auto-merge; explicit series_id selection | D-09 |
| Book ID Semantics | Stage 4 frozen definition unchanged | D-10 |
| Concurrent Books | DISALLOWED in Stage 5 | Spec §14.2 |

### Next Steps:

1. Owner reviews and resolves Owner Decisions in §15
2. Upon resolution → Update this audit with confirmed decisions
3. Then → Begin Batch 5.7 Implementation per Implementation Task

---

*End of Preflight Audit. No production code modified. Awaiting Owner decisions for Batch 5.7 authorization.*
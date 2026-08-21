# P0 Stage 5 Batch 5.7 — Series Orchestration Implementation Task

**Baseline Commit:** `0bfa97d` (HEAD = origin/main, Batch 5.6 delivered)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` (§15, §16, §17, §28, §29)
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md` (Batch 5.7)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_BATCH5_7_PREFLIGHT_AUDIT.md`
**Task Status:** Specification Defined — **BLOCKED — Owner Decisions Required**
**Implementation Status:** NOT STARTED

---

## 1. Objective

Implement the **Series Orchestration** layer for P0 Stage 5 Series Continuity.

**Deliverables:**
- New module `core/series_orchestration/` with:
  - `coordinator.py` — `SeriesTranslationCoordinator` (high-level workflow orchestration)
  - `workflow.py` — Multi-book workflow state machine (`BookWorkflowState`, `SeriesWorkflowState`)
  - `cli_integration.py` — CLI commands: `series create`, `add-book`, `promote-book`, `status`, `resume`
  - `runtime_integration.py` — `TranslationRuntime` series context injection (`build_series_context`, `inject_series_context`)
  - `validation.py` — Workflow validation, cross-series isolation enforcement
- `TranslationRuntime` additive integration: optional `series_id`, `book_identity` parameters in `translate_txt()`, `translate_package()`
- `ntpe_launcher.py` additive integration: series subcommands
- Passion 6-book scenario end-to-end validation
- Cross-series isolation hard gates (CSI-05) at orchestration level

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **SeriesTranslationCoordinator** | High-level orchestration: create series, add book, translate book, promote book, resume |
| **Workflow State Machine** | `BookWorkflowState`, `SeriesWorkflowState` — book lifecycle, series lifecycle, next actions |
| **CLI Integration** | `ntpe series create`, `add-book`, `promote-book`, `status`, `list`, `resume` |
| **Runtime Integration** | `build_series_context()`, `inject_series_context()` for TranslationRuntime |
| **TranslationRuntime Extension** | Additive optional `series_id`, `book_identity` to `translate_txt()`, `translate_package()` |
| **Launcher Extension** | Series subcommands in `ntpe_launcher.py` |
| **Validation & Isolation** | Cross-series isolation enforcement, workflow validation, CSI-05 hard gates |
| **Backward Compatibility** | TXT/EPUB workflows without series_id work identically |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Modify `core/translation_runtime/` core TXT/batch logic | **FROZEN** (only additive optional params) |
| Modify `core/translation_pipeline/` | **FROZEN** |
| Modify `core/book_intake/` | **FROZEN** |
| Modify `core/production_runtime/` | **FROZEN** |
| Modify `lts/` | **FROZEN** |
| Modify `core/character_memory_v2/` core models/store/lifecycle | **FROZEN** |
| Modify `core/context_scene_memory/` core models/store/lifecycle | **FROZEN** |
| Modify `core/entity_resolver/` core models/injector/resolve logic | **FROZEN** |
| Modify `core/knowledge_runtime/` core merger/snapshot/resolver | **FROZEN** |
| Modify `core/runtime_checkpoint/` | **FROZEN** |
| Modify `core/series_identity/`, `core/series_memory/`, `core/series_entity_registry/`, `core/series_checkpoint/` | **FROZEN** (already implemented) |
| Any Frozen Contract modification | **FROZEN** |
| Feature flag activation | Forbidden |
| Provider/Network/Translation execution in tests | Forbidden |

---

## 4. Architecture

### 4.1 Module Structure

```
core/series_orchestration/
├── __init__.py
├── coordinator.py              # SeriesTranslationCoordinator
├── workflow.py                 # BookWorkflowState, SeriesWorkflowState
├── cli_integration.py          # CLI command implementations
├── runtime_integration.py      # build_series_context, inject_series_context
└── validation.py               # Workflow validation, cross-series isolation
```

### 4.2 Dependency / Ownership Diagram

```
SeriesTranslationCoordinator (Orchestrator)
    ├── SeriesRegistry (SeriesManifest authority)
    ├── SeriesMemoryStore (Canonical facts, hydration, promotion)
    ├── SeriesEntityRegistry (Canonical entities, resolver integration)
    ├── SeriesGlossary (Canonical terms, build/merge/promotion)
    ├── SeriesKnowledge (Novel tier population)
    ├── SeriesCheckpointManager (Recovery orchestration)
    │
    ├── TranslationRuntime (Execution - additive series context)
    │   ├── translate_txt(series_id, book_identity)
    │   └── translate_package(series_id, book_identity)
    │
    ├── BookIntake (Book identity, manifest)
    │
    ├── Character Memory v2 (BookMemoryStore hydration)
    ├── Context/Scene Memory (BookContextStore)
    │
    └── CLI Integration (User commands)
        ├── series create "Name"
        ├── series add-book "Name" file.txt
        ├── series promote-book "Name" --book 1
        ├── translate --series "Name" --book 1
        └── series status "Name"
```

**Forbidden:** Bidirectional dependency `SeriesTranslationCoordinator` ↔ frozen modules internals

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.series_identity` | Internal | `SeriesManifest`, `SeriesRegistry`, `SeriesIdentity` |
| `core.series_memory` | Internal | `SeriesMemoryStore`, `SeriesCharacterRecord`, hydration, promotion |
| `core.series_entity_registry` | Internal | `SeriesEntityRegistry`, `hydrate_resolver()`, `promote_from_resolver()` |
| `core.glossary_builder` | Internal | `SeriesGlossary`, `build_series_glossary()`, `merge_into_series_glossary()` |
| `core.knowledge_runtime` | Internal | `KnowledgeRuntimeManager.load_series_knowledge()`, `populate_volume_tier()` |
| `core.series_checkpoint` | Internal | `SeriesCheckpointManager`, `resume_series()`, `resume_book_in_series()`, `start_new_book_in_series()` |
| `core.translation_runtime` | Internal | `TranslationRuntime` (additive series context params) |
| `core.book_intake` | Internal | `BookIntakeProcessor`, `compute_book_identity` |
| `core.character_memory_v2.persistence` | Internal | `load_or_create_character_memory()`, `get_memory_file_path()` |
| `core.context_scene_memory.persistence` | Internal | `get_context_memory_file_path()` |

**No dependencies on:** `core.translation_pipeline`, `core.production_runtime`, `core.runtime_orchestrator`, `lts/`

---

## 5. Data Models

### 5.1 Workflow State (in `workflow.py`)

```python
from dataclasses import dataclass
from typing import Tuple, List
from datetime import datetime

@dataclass(frozen=True)
class BookWorkflowState:
    """Runtime state of a book within a series translation workflow."""
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

    def to_dict(self) -> dict:
        return {
            "volume_number": self.volume_number,
            "book_identity": self.book_identity,
            "status": self.status,
            "hydration_done": self.hydration_done,
            "translation_started_at": self.translation_started_at,
            "translation_completed_at": self.translation_completed_at,
            "promotion_completed_at": self.promotion_completed_at,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class SeriesWorkflowState:
    """Runtime state of an entire series translation workflow."""
    series_id: str
    series_name: str
    lifecycle_status: str  # "CREATED" | "ACTIVE" | "COMPLETED" | "ARCHIVED"
    books: Tuple[BookWorkflowState, ...]
    next_volume_number: int
    next_actions: List[str]  # e.g., ["translate:volume_2", "promote:volume_1"]

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "series_name": self.series_name,
            "lifecycle_status": self.lifecycle_status,
            "books": [b.to_dict() for b in self.books],
            "next_volume_number": self.next_volume_number,
            "next_actions": self.next_actions,
        }


@dataclass(frozen=True)
class SeriesCreateResult:
    series_id: str
    manifest: Any  # SeriesManifest
    manifest_path: Any  # Path


@dataclass(frozen=True)
class BookAddResult:
    volume_number: int
    book_identity: str
    book_entry: Any  # SeriesBookEntry
    manifest: Any  # SeriesManifest
    manifest_path: Any  # Path


@dataclass(frozen=True)
class TranslationReport:
    series_id: str
    book_identity: str
    volume_number: int
    status: str  # "success" | "failed" | "interrupted"
    chunks_translated: int
    total_chunks: int
    hydration_summary: Any | None  # HydrationReport from series_memory
    checkpoint_id: str | None
    error: str | None


@dataclass(frozen=True)
class PromotionReport:
    series_id: str
    book_identity: str
    volume_number: int
    promotion_results: Tuple[Any, ...]  # SeriesAddResult from series_memory + series_entity + glossary
    memory_promotion: Any  # Tuple[SeriesAddResult, ...] from series_memory.promote_from_book()
    entity_promotion: Any  # Tuple[AddResult, ...] from series_entity.promote_from_resolver()
    glossary_promotion: Any  # Tuple[GlossaryPromotionRecord, ...] from merge_into_series_glossary()
    series_memory_hash: str
    series_entity_registry_hash: str
    series_glossary_hash: str
    series_knowledge_hash: str
    series_checkpoint_hash: str


@dataclass(frozen=True)
class SeriesStatusReport:
    series_id: str
    series_name: str
    lifecycle_status: str
    workflow_state: SeriesWorkflowState
    manifest: Any  # SeriesManifest
    latest_checkpoint: Any | None  # SeriesCheckpoint
```

### 5.2 Runtime Integration Models (in `runtime_integration.py`)

```python
from dataclasses import dataclass
from typing import Any

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
    series_manifest: Any  # SeriesManifest

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "volume_number": self.volume_number,
            "series_memory_hash": self.series_memory_hash,
            "series_entity_registry_hash": self.series_entity_registry_hash,
            "series_glossary_hash": self.series_glossary_hash,
            "series_knowledge_hash": self.series_knowledge_hash,
            "book_memory_hash": self.book_memory_hash,
            "book_context_hash": self.book_context_hash,
            "session_checkpoint_id": self.session_checkpoint_id,
        }
```

### 5.3 Validation Exceptions (in `validation.py`)

```python
class SeriesOrchestrationValidationError(Exception):
    """Raised when Series orchestration validation fails."""
    pass


class SeriesOrchestrationIsolationError(Exception):
    """Raised when cross-series isolation violation detected (fail-closed)."""
    def __init__(self, operation: str, expected_series_id: str, actual_series_id: str):
        super().__init__(
            f"Cross-series isolation violation in {operation}: "
            f"expected series_id={expected_series_id}, got series_id={actual_series_id}"
        )
        self.operation = operation
        self.expected_series_id = expected_series_id
        self.actual_series_id = actual_series_id


class SeriesWorkflowError(Exception):
    """Raised when workflow state transition is invalid."""
    pass


class SeriesBookNotFoundError(Exception):
    """Raised when book not found in series."""
    pass
```

---

## 6. Series Orchestration Identity Semantics

### 6.1 Namespace Isolation Rules

| Layer | Mechanism |
|-------|-----------|
| **File Path** | All series artifacts under `output/series/{series_id}/` |
| **Manifest Key** | All operations require explicit `series_id` |
| **CLI Commands** | Series name resolved to `series_id` via Registry |
| **Translation Context** | `series_id` + `book_identity` passed to runtime |
| **Checkpoint** | Series checkpoint includes all book/session refs |
| **Recovery** | `series_id` required for all resume operations |

### 6.2 CLI Command Design (Owner Confirmed)

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

## 7. SeriesTranslationCoordinator (in `coordinator.py`)

### 7.1 Core Methods

```python
class SeriesTranslationCoordinator:
    """High-level orchestration for series translation workflows."""

    version = "p0-stage5-batch5.7"

    def __init__(
        self,
        output_root: Path,
        series_registry: Any,  # SeriesRegistry
        series_memory_store: Any,  # SeriesMemoryStore
        series_entity_registry: Any,  # SeriesEntityRegistry
        series_glossary: Any,  # SeriesGlossary
        series_knowledge: Any,  # SeriesKnowledge
        series_checkpoint_manager: Any,  # SeriesCheckpointManager
        translation_runtime: Any,  # TranslationRuntime
    ):
        self.output_root = output_root
        self.series_registry = series_registry
        self.series_memory_store = series_memory_store
        self.series_entity_registry = series_entity_registry
        self.series_glossary = series_glossary
        self.series_knowledge = series_knowledge
        self.series_checkpoint_manager = series_checkpoint_manager
        self.translation_runtime = translation_runtime

    def create_series(
        self,
        user_defined_series_key: str,
        series_name: str | None = None,
    ) -> SeriesCreateResult:
        """Create new series. Returns SeriesManifest."""
        # 1. Validate series_id doesn't exist
        # 2. Create series via SeriesRegistry
        # 3. Create empty SeriesMemoryStore, SeriesEntityRegistry, SeriesGlossary, SeriesKnowledge
        # 4. Return SeriesCreateResult

    def add_book(
        self,
        series_id: str,
        source_path: Path,
        title: str | None = None,
    ) -> BookAddResult:
        """Add book to series. Returns BookRef with volume_number."""
        # 1. Validate series_id exists
        # 2. Compute book_identity from source_path + series_name
        # 3. Process book_intake to get BookIntakeManifest
        # 4. Add book to SeriesRegistry (updates manifest, assigns volume_number)
        # 5. Create empty BookMemoryStore, BookContextStore (will be hydrated at translation start)
        # 6. Create SeriesCheckpoint with new book reference (status="pending")
        # 7. Return BookAddResult

    def translate_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        dry_run: bool = False,
        options: Any | None = None,
    ) -> TranslationReport:
        """Translate a specific book in series with series context hydration."""
        # 1. Validate series_id, volume_number exist
        # 2. Get book_identity from SeriesManifest
        # 3. Set book status to "in_progress" in SeriesManifest
        # 4. Build SeriesContext via runtime_integration.build_series_context()
        # 5. Inject series context into TranslationRuntime
        # 6. Call translation_runtime.translate_txt() with series_id, book_identity
        # 7. On completion: set book status to "completed"
        # 8. Create SeriesCheckpoint
        # 9. Return TranslationReport

    def promote_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        approval_gate: bool = True,
    ) -> PromotionReport:
        """Promote completed book facts to series (MANUAL gate)."""
        # 1. Validate series_id, volume_number, book status = "completed"
        # 2. Load BookMemoryStore, BookContextStore
        # 3. Get EntityResolver user_overrides from book translation
        # 4. Promote: SeriesMemoryStore.promote_from_book() (MANUAL gate)
        # 5. Promote: SeriesEntityRegistry.promote_from_resolver() (MANUAL gate)
        # 6. Promote: merge_into_series_glossary() (MANUAL gate)
        # 7. Repopulate KnowledgeRuntime Novel tier
        # 8. Update all manifest hashes
        # 9. Set book status to "promoted"
        # 10. Create SeriesCheckpoint
        # 11. Return PromotionReport

    def get_series_status(self, series_id: str) -> SeriesStatusReport:
        """Get current series status: books, progress, next actions."""
        # 1. Load SeriesManifest
        # 2. Load latest SeriesCheckpoint
        # 3. Build SeriesWorkflowState from manifest + checkpoint
        # 4. Determine next_actions
        # 5. Return SeriesStatusReport

    def resume_series(self, series_id: str) -> SeriesResumeReport:
        """Resume entire series from checkpoint."""
        # Delegate to SeriesCheckpointManager.resume_series()

    def resume_book(self, series_id: str, volume_number: int) -> BookResumeReport:
        """Resume specific book in series."""
        # Delegate to SeriesCheckpointManager.resume_book_in_series()
```

---

## 8. Runtime Integration (in `runtime_integration.py`)

### 8.1 Build Series Context

```python
def build_series_context(
    series_id: str,
    book_identity: str,
    output_root: Path,
    series_registry: Any,  # SeriesRegistry
    series_memory_store: Any,  # SeriesMemoryStore
    series_entity_registry: Any,  # SeriesEntityRegistry
    series_glossary: Any,  # SeriesGlossary
    series_knowledge: Any,  # SeriesKnowledge
    series_checkpoint_manager: Any,  # SeriesCheckpointManager
) -> SeriesContext:
    """
    Build series context for translation runtime.

    1. Load SeriesManifest → get book volume_number, source_path
    2. Load SeriesCheckpoint → get BookCheckpointRef for this book
    3. Validate all hashes (fail-closed)
    4. Get book memory hash, book context hash from checkpoint
    5. Get session checkpoint ID from checkpoint
    6. Return SeriesContext
    """
```

### 8.2 Inject Series Context

```python
def inject_series_context(
    runtime: Any,  # TranslationRuntime
    series_context: SeriesContext,
    output_root: Path,
    series_memory_store: Any,  # SeriesMemoryStore
    series_entity_registry: Any,  # SeriesEntityRegistry
    series_glossary: Any,  # SeriesGlossary
    series_knowledge: Any,  # SeriesKnowledge
    book_identity: str,
) -> None:
    """
    Inject series context into TranslationRuntime.

    1. Hydrate BookMemoryStore from SeriesMemoryStore
    2. Load BookContextStore (book-local)
    3. Get EntityResolver user_overrides from SeriesEntityRegistry.hydrate_resolver()
    4. Populate KnowledgeMerger Novel tier from SeriesKnowledge
    5. Populate KnowledgeMerger Volume tier from BookMemoryStore + BookGlossary
    6. Set GlossaryBuilder locked_dictionary from SeriesGlossary.get_locked_dictionary()
    7. Store series_context in runtime for use during translation
    """
```

---

## 9. CLI Integration (in `cli_integration.py`)

### 9.1 Command Implementations

```python
def cmd_series_create(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
    output_root: Path,
) -> SeriesCreateResult:
    """ntpe series create "Series Name" """
    user_key = series_name.strip()
    return coordinator.create_series(user_key, series_name)


def cmd_series_list(
    coordinator: SeriesTranslationCoordinator,
) -> list[Any]:  # List[SeriesIdentity]
    """ntpe series list"""
    return coordinator.series_registry.list_all()


def cmd_series_status(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
) -> SeriesStatusReport:
    """ntpe series status "Series Name" """
    # Resolve series name to series_id if needed
    return coordinator.get_series_status(series_id)


def cmd_series_rename(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
    new_name: str,
) -> Any:  # SeriesManifest
    """ntpe series rename "Old Name" "New Name" """
    return coordinator.series_registry.update_name(series_id, new_name)


def cmd_series_add_book(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
    source_path: Path,
    title: str | None = None,
) -> BookAddResult:
    """ntpe series add-book "Series Name" path/to/file.txt"""
    return coordinator.add_book(series_id, source_path, title)


def cmd_series_promote_book(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
    volume_number: int,
) -> PromotionReport:
    """ntpe series promote-book "Series Name" --book 1"""
    return coordinator.promote_book(series_id, volume_number)


def cmd_translate_with_series(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
    volume_number: int,
    *,
    dry_run: bool = False,
    options: Any | None = None,
) -> TranslationReport:
    """ntpe translate --series "Series Name" --book 1"""
    return coordinator.translate_book(series_id, volume_number, dry_run=dry_run, options=options)


def cmd_series_resume(
    coordinator: SeriesTranslationCoordinator,
    series_id: str,
    volume_number: int | None = None,
) -> Any:  # SeriesResumeReport | BookResumeReport
    """ntpe series resume "Series Name" [--book 2]"""
    if volume_number:
        return coordinator.resume_book(series_id, volume_number)
    return coordinator.resume_series(series_id)
```

---

## 10. TranslationRuntime Additive Integration

### 10.1 Changes to `core/translation_runtime/runtime.py`

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
        # Import locally to avoid circular dependency
        from core.series_orchestration.runtime_integration import (
            build_series_context,
            inject_series_context,
        )
        # Build coordinator dependencies
        # This requires access to series stores - passed via runtime initialization or factory
        series_context = build_series_context(
            series_id=series_id,
            book_identity=book_identity,
            output_root=self.root,
            series_registry=...,  # Need access to series registry
            series_memory_store=...,
            series_entity_registry=...,
            series_glossary=...,
            series_knowledge=...,
            series_checkpoint_manager=...,
        )
        inject_series_context(self, series_context, ...)
    # ... existing TXT translation logic unchanged
    from lts.txt_translation_runtime import translate_txt
    return translate_txt(options, root=self.root)

def translate_package(
    self,
    package: dict,
    package_path: str | Path | None = None,
    series_id: str | None = None,
    book_identity: str | None = None,
) -> dict[str, Any]:
    if series_id and book_identity:
        from core.series_orchestration.runtime_integration import (
            build_series_context,
            inject_series_context,
        )
        series_context = build_series_context(...)
        inject_series_context(self, series_context, ...)
    # ... existing package translation logic unchanged
    return self.provider.translate_package(package, package_path=package_path)
```

### 10.2 TranslationRuntime Initialization Extension

```python
# In TranslationRuntime.__init__, add optional series stores for lazy injection
def __init__(self, root: str | Path | None = None, api_key: str | None = None):
    # ... existing init ...
    # Add series stores for series-aware translation (set by coordinator)
    self._series_registry: Any = None
    self._series_memory_store: Any = None
    self._series_entity_registry: Any = None
    self._series_glossary: Any = None
    self._series_knowledge: Any = None
    self._series_checkpoint_manager: Any = None

def set_series_context(
    self,
    series_registry: Any,
    series_memory_store: Any,
    series_entity_registry: Any,
    series_glossary: Any,
    series_knowledge: Any,
    series_checkpoint_manager: Any,
) -> None:
    """Set series stores for series-aware translation (called by coordinator)."""
    self._series_registry = series_registry
    self._series_memory_store = series_memory_store
    self._series_entity_registry = series_entity_registry
    self._series_glossary = series_glossary
    self._series_knowledge = series_knowledge
    self._series_checkpoint_manager = series_checkpoint_manager
```

---

## 11. Launcher Integration (Additive)

### 11.1 Changes to `ntpe_launcher.py`

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ntpe_launcher.py",
        description="NTPE 2.0 translation launcher product foundation",
    )
    # ... existing args ...

    # Add series subcommands
    subparsers = parser.add_subparsers(dest="command", help="Series commands")
    series_parser = subparsers.add_parser("series", help="Series management")
    series_subparsers = series_parser.add_subparsers(dest="series_command")

    # series create
    create_parser = series_subparsers.add_parser("create", help="Create new series")
    create_parser.add_argument("name", help="Series name")

    # series list
    series_subparsers.add_parser("list", help="List all series")

    # series status
    status_parser = series_subparsers.add_parser("status", help="Show series status")
    status_parser.add_argument("name", help="Series name")

    # series rename
    rename_parser = series_subparsers.add_parser("rename", help="Rename series")
    rename_parser.add_argument("old_name", help="Current series name")
    rename_parser.add_argument("new_name", help="New series name")

    # series add-book
    add_book_parser = series_subparsers.add_parser("add-book", help="Add book to series")
    add_book_parser.add_argument("name", help="Series name")
    add_book_parser.add_argument("source", type=Path, help="Source file path")
    add_book_parser.add_argument("--title", help="Book title")

    # series promote-book
    promote_parser = series_subparsers.add_parser("promote-book", help="Promote book to series")
    promote_parser.add_argument("name", help="Series name")
    promote_parser.add_argument("--book", type=int, required=True, help="Volume number")

    # series resume
    resume_parser = series_subparsers.add_parser("resume", help="Resume series/book")
    resume_parser.add_argument("name", help="Series name")
    resume_parser.add_argument("--book", type=int, help="Volume number to resume")

    # translate with series
    translate_parser = subparsers.add_parser("translate", help="Translate with series context")
    translate_parser.add_argument("--series", help="Series name")
    translate_parser.add_argument("--book", type=int, help="Volume number")
    # ... existing translate args ...

    return parser
```

---

## 12. Cross-Series Isolation (Hard Enforcement)

### 12.1 Validation Rules (in `validation.py`)

```python
def validate_series_operation(
    operation: str,
    expected_series_id: str,
    actual_series_id: str,
) -> None:
    """Validate series_id matches expected (fail-closed)."""
    if expected_series_id != actual_series_id:
        raise SeriesOrchestrationIsolationError(operation, expected_series_id, actual_series_id)


def validate_book_in_series(
    series_id: str,
    book_identity: str,
    series_manifest: Any,
) -> Any:  # SeriesBookEntry
    """Validate book belongs to series."""
    book = series_manifest.get_book_by_identity(book_identity)
    if book is None:
        raise SeriesBookNotFoundError(f"Book {book_identity} not in series {series_id}")
    return book


def validate_workflow_transition(
    current_status: str,
    new_status: str,
    operation: str,
) -> None:
    """Validate book workflow state transition."""
    valid_transitions = {
        "pending": {"in_progress", "failed", "archived"},
        "in_progress": {"completed", "failed", "archived"},
        "completed": {"promoted", "archived"},
        "promoted": {"archived"},
        "failed": {"archived"},
        "archived": set(),
    }
    if new_status not in valid_transitions.get(current_status, set()):
        raise SeriesWorkflowError(
            f"Invalid workflow transition in {operation}: {current_status} -> {new_status}"
        )
```

### 12.2 Hard Failure Cases (All MUST Fail)

| Case | Validation Point |
|------|------------------|
| Translate with series_id not matching book | `translate_book()` → `validate_book_in_series()` |
| Promote book from wrong series | `promote_book()` → `validate_book_in_series()` |
| Resume series with mismatched checkpoint series_id | `resume_series()` → `validate_cross_series_isolation()` |
| Add book to archived series | `add_book()` → `SeriesRegistry` validation |
| CLI command with series name resolving to wrong series_id | `cli_integration` → `SeriesRegistry.get()` |

---

## 13. CSI-05 + SO-01~14 Acceptance Tests (Hard Gates)

> **All MUST PASS. Any failure → Batch 5.7 not accepted.**

| Test ID | Description | Verification |
|---------|-------------|--------------|
| **CSI-05** | Series A orchestration ≠ Series B | Verify no cross-series data access in coordinator, CLI, runtime |
| **SO-01** | Series create → manifest | Manifest created, series_id valid |
| **SO-02** | Add book → volume_number=1 | BookRef created, manifest updated |
| **SO-03** | Translate with series → hydrated | BookMemoryStore has series canonical facts |
| **SO-04** | Promote book → SeriesMemoryStore updated | Canonical facts in SeriesMemoryStore, manifest hashes updated |
| **SO-05** | Full Passion 6-book scenario PASS | Book 1→6 continuous with character/glossary continuity |
| **SO-06** | Cross-series contamination test | Series A "李某" ≠ Series B "李某" — 0 leaks |
| **SO-07** | Single-book TXT regression | TXT translation without series_id works identically |
| **SO-08** | Single-book EPUB regression | EPUB workflow without series_id works identically |
| **SO-09** | Series resume → restores all levels | All stores restored, books resumable |
| **SO-10** | Book resume in series → hydration + session | Book hydrated, session restored, chunk progress correct |
| **SO-11** | Provider/Network/Translation = 0/0/0 | Verified in test runs |
| **SO-12** | Root hygiene | No files in repo root |
| **SO-13** | Frozen contract isolation | All frozen modules unchanged |
| **SO-14** | CLI series commands work | All commands execute, output valid |

---

## 14. Test Requirements

### 14.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_series_create` | Create series via coordinator |
| `test_add_book` | Add book to series, volume_number assigned |
| `test_translate_book_hydrated` | Translation with series context injects canonical facts |
| `test_promote_book_manual_gate` | Promotion requires approval_gate=True |
| `test_promote_book_conflict_detection` | Different values → CONFLICT |
| `test_get_series_status` | Status report includes workflow state, next_actions |
| `test_resume_series` | Full series resume from checkpoint |
| `test_resume_book_in_series` | Single book resume with hydration |
| `test_build_series_context` | Context includes all hashes, book refs |
| `test_inject_series_context` | Runtime receives hydration, resolver overrides, knowledge tiers |
| `test_cli_series_create` | CLI command creates series |
| `test_cli_add_book` | CLI command adds book |
| `test_cli_promote_book` | CLI command promotes book |
| `test_cli_translate_series` | CLI translate with series context |
| `test_cross_series_isolation_coordinator` | Coordinator rejects cross-series operations |
| `test_cross_series_isolation_runtime` | Runtime rejects mismatched series_id |
| `test_cross_series_isolation_cli` | CLI rejects cross-series commands |
| `test_backward_compat_txt` | TXT translation without series_id unchanged |
| `test_backward_compat_epub` | EPUB workflow without series_id unchanged |
| `test_deterministic_context` | Same inputs → same SeriesContext |

### 14.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_context_deterministic` | 1000 |
| `test_workflow_state_transitions` | 1000 |

### 14.3 Integration Tests

| Test | Description |
|------|-------------|
| `test_passion_6book_scenario` | Book 1→6 continuous translation with continuity |
| `test_cross_series_no_leakage` | Series A and B isolated, no data leakage |
| `test_full_series_resume_after_restart` | Process restart simulation |
| `test_existing_checkpoint_compat` | Pre-Stage 5 checkpoints load, work without series |

---

## 15. Frozen Contracts Audit

**Batch 5.7 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | No touch |
| Context Pipeline Contract | No touch |
| Prompt Pipeline Contract | No touch |
| Plugin Contract | No touch |
| Production Pipeline Contract | No touch |
| Translation Runtime Contract | Additive params only |
| Intelligence Contract | No touch |
| Knowledge Contract | No touch |
| Snapshot Contract | No touch |
| Character Memory v2 core | No touch |
| Context/Scene Memory core | No touch |
| Entity Resolver core | No touch |
| Knowledge Runtime core | No touch |
| Runtime Checkpoint core | No touch |
| Production Runtime Checkpoint | No touch |
| Translation Session Checkpoint | No touch |
| All 9 Foundation Frozen Contracts | No touch |

**New Contract Created by Batch 5.7:**
- **Series Orchestration Contract** (`core/series_orchestration/`) — to be added to Foundation Manifest in Batch 5.9

---

## 16. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/translation_runtime/runtime.py` core logic | **FROZEN** (only additive optional params) |
| `core/translation_pipeline/` | **FROZEN** |
| `core/book_intake/` | **FROZEN** |
| `core/production_runtime/` | **FROZEN** |
| `lts/` | **FROZEN** |
| `core/character_memory_v2/` models/store/lifecycle/selection/validation | **FROZEN** |
| `core/context_scene_memory/` models/store/lifecycle/scene_state/context_selection | **FROZEN** |
| `core/entity_resolver/` models/injector/_resolve_single core logic | **FROZEN** |
| `core/knowledge_runtime/` models/merger/snapshot/resolver | **FROZEN** |
| `core/runtime_checkpoint/` | **FROZEN** |
| `core/series_identity/` | **FROZEN** (complete) |
| `core/series_memory/` | **FROZEN** (complete) |
| `core/series_entity_registry/` | **FROZEN** (complete) |
| `core/series_checkpoint/` | **FROZEN** (complete) |
| Any Frozen Contract (9 existing) | **FROZEN** |
| Feature flag changes | **FROZEN** |
| TXT/EPUB/Translation behavior (without series_id) | **FROZEN** |
| Provider/Network/Translation execution | **FROZEN** |

---

## 17. Validation Gates

**All must PASS before Batch 5.7 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-05 + SO-01~14 tests PASS
- [ ] Batch 5.7 Acceptance Test Matrix (§13) all PASS
- [ ] No regression in existing pytest tests (all prior Stage 5 batches)
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)
- [ ] Passion 6-book scenario PASS

---

## 18. Git Scope Rules

**Allowed Changes:**

- **NEW** `core/series_orchestration/` (complete module: `__init__.py`, `coordinator.py`, `workflow.py`, `cli_integration.py`, `runtime_integration.py`, `validation.py`)
- **ADDITIVE** `core/translation_runtime/runtime.py` — Optional `series_id`, `book_identity` parameters in `translate_txt()`, `translate_package()`; `set_series_context()` method
- **ADDITIVE** `ntpe_launcher.py` — Series subcommands
- **NEW** `tests/series/test_batch5_7_*.py` (test files)

**Forbidden:**

- Any modification to existing production code outside allowed additive changes
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 19. Delivery Rules

**Deliverables (working tree changes only, no staging):**

1. New `core/series_orchestration/__init__.py`
2. New `core/series_orchestration/coordinator.py`
3. New `core/series_orchestration/workflow.py`
4. New `core/series_orchestration/cli_integration.py`
5. New `core/series_orchestration/runtime_integration.py`
6. New `core/series_orchestration/validation.py`
7. Additive changes to `core/translation_runtime/runtime.py` (series context params + `set_series_context()`)
8. Additive changes to `ntpe_launcher.py` (series subcommands)
9. `tests/series/test_batch5_7_*.py`
10. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 20. Rollback Boundary

**Clean Rollback:**

- Delete `core/series_orchestration/` directory
- Revert `core/translation_runtime/runtime.py` to baseline (remove series params, `set_series_context()`)
- Revert `ntpe_launcher.py` to baseline (remove series subcommands)
- Delete `tests/series/test_batch5_7_*.py`

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules
- **All Batch 5.1-5.6 modules UNCHANGED — no revert needed**

---

## 21. Provider / Network / Translation Policy

- **ZERO** provider calls (uses existing mock/dry-run paths)
- **ZERO** network requests
- **ZERO** real translation executions (test uses mock provider or dry-run)
- Pure offline deterministic computation only

---

## 22. Root Hygiene

**No files in repository root:**
- `*.py`, `*.ps1`, `*.bat`, `*.json`, `*.txt`, `*.log`

**Allowed locations:**
- `core/series_orchestration/` — implementation
- `core/translation_runtime/` — additive runtime changes
- `ntpe_launcher.py` — additive CLI changes
- `tests/series/` — tests
- `docs/governance/rm8/` — docs
- `artifacts/` — diagnostic output only

---

## 23. Completion Criteria

**Batch 5.7 Complete When:**

1. All §14 unit tests PASS
2. All §14 property-based tests PASS (1000 iterations each)
3. All §13 CSI-05 + SO-01~14 tests PASS
4. All §17 Validation gates PASS
5. Git status shows only allowed new files + allowed additive changes
6. No production code modified outside allowed additive changes
7. No Frozen Contracts modified
8. **All Batch 5.1-5.6 modules unchanged**
9. Passion 6-book scenario PASS

**Status Report:** "P0 Stage 5 Batch 5.7 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 24. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Preflight complete, models defined, integration points specified, owner decisions identified | 2026-08-22 |
| Owner | Authorization to proceed (decisions resolved) | ____________ |
| QA | CSI-05 + SO-01~14 test matrix & Acceptance Test Matrix accepted | ____________ |

---

## 25. Owner Decisions — REQUIRED

| Decision | Options | Status |
|----------|---------|--------|
| **CLI Command Design** | Proposed in §6.2 | **PENDING OWNER CONFIRMATION** |
| **TranslationRuntime Series Parameters** | Add optional `series_id`, `book_identity` to `translate_txt()`, `translate_package()` | **PENDING OWNER CONFIRMATION** |
| **Launcher Integration** | Add series subcommands to ntpe_launcher.py | **PENDING OWNER CONFIRMATION** |
| **Dry-Run Series Support** | Extend `--dry-run` for series workflows | **PENDING OWNER CONFIRMATION** |
| **Passion 6-Book Test Data** | Need actual Passion 6-book test corpus | **PENDING OWNER CONFIRMATION** |

---

*End of Batch 5.7 Implementation Task. Specification COMPLETE — Owner decisions required — BLOCKED pending Owner authorization.*
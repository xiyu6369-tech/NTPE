# P0 Stage 5 Batch 5.6 — Series Checkpoint Hierarchy Implementation Task

**Baseline Commit:** `ff2d2cb43205b10dcc82ad7e4554fbd170b70c6b` (HEAD = origin/main)
**Formal Specification:** `docs/governance/rm8/P0_STAGE5_FORMAL_SPECIFICATION.md` (§11, §12, §13, §24, §25, §28)
**Batch Plan:** `docs/governance/rm8/P0_STAGE5_BATCH_PLAN.md` (Batch 5.6)
**Preflight Audit:** `docs/governance/rm8/P0_STAGE5_BATCH5_6_PREFLIGHT_AUDIT.md`
**Task Status:** Specification Defined — **READY FOR OWNER AUTHORIZATION**
**Implementation Status:** NOT STARTED

---

## 1. Objective

Implement the **Series Checkpoint Hierarchy** for P0 Stage 5 Series Continuity.

**Deliverables:**
- New module `core/series_checkpoint/` with:
  - `models.py` — `SeriesCheckpoint`, `BookCheckpointRef`, `SessionCheckpointRef`, `CheckpointCreationReport`, `SeriesResumeReport`, `BookResumeReport`, `BookStartReport`
  - `manager.py` — `SeriesCheckpointManager` (creation, persistence, recovery orchestration)
  - `persistence.py` — Load/save `series_checkpoint_{series_id}.json` with SHA-256 integrity
  - `recovery.py` — Recovery orchestration (`resume_series`, `resume_book_in_series`, `start_new_book_in_series`)
  - `validation.py` — Checkpoint schema validation, hash integrity, fail-closed behavior
- SeriesManifest integration via existing `series_checkpoint_hash` derived field (populate via `SeriesRegistry.update_series_checkpoint_hash()`)
- 4-level hierarchy: Series → Book → Session → Chunk
- Cross-series isolation via `series_id` namespace
- CSI-05 hard gate for checkpoint isolation

---

## 2. Scope (In-Scope)

| Component | Description |
|-----------|-------------|
| **SeriesCheckpoint Model** | Series-level checkpoint with all Series artifact hashes + book/session refs |
| **BookCheckpointRef Model** | Reference to book memory/context hashes + latest session |
| **SessionCheckpointRef Model** | Reference to session chunk progress + context hash |
| **SeriesCheckpointManager** | Create, save, load, list, validate checkpoints |
| **Persistence** | Deterministic JSON (`series_checkpoint_{series_id}.json`) with canonical serialization + SHA-256 fingerprint |
| **Recovery Orchestration** | `resume_series()`, `resume_book_in_series()`, `start_new_book_in_series()` |
| **Validation & Integrity** | Schema validation, fingerprint verification, book/session hash verification, fail-closed |
| **Manifest Integration** | Call `SeriesRegistry.update_series_checkpoint_hash()` after checkpoint creation |
| **Cross-Series Isolation** | Enforce `series_id` namespace in file paths, manifest, all operations |
| **Frozen Checkpoint Integration** | Reference existing `runtime_checkpoint`, `production_runtime`, `translation_session` checkpoints by hash/ID |

---

## 3. Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Modify `core/runtime_checkpoint/` | **FROZEN** (RM-6.3.2) |
| Modify `core/production_runtime/checkpoint.py` | **FROZEN** |
| Modify `core/translation_session/session_checkpoint.py` | **FROZEN** |
| Modify `core/series_identity/manifest.py` | Field already exists, only additive call to registry |
| Modify `core/series_identity/registry.py` | Method already exists, only additive call |
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
core/series_checkpoint/
├── __init__.py
├── models.py                 # SeriesCheckpoint, BookCheckpointRef, SessionCheckpointRef, reports
├── manager.py                # SeriesCheckpointManager
├── persistence.py            # Load/save with integrity verification
├── recovery.py               # Recovery orchestration
└── validation.py             # Schema validation, hash integrity, exceptions
```

### 4.2 Dependency / Ownership Diagram

```
SeriesCheckpointManager (Orchestrator)
    ├── SeriesCheckpoint (Series-Level Artifact)
    │   ├── persistence (series_checkpoint_{series_id}.json)
    │   ├── validation (schema, fingerprint, cross-series, book/session hashes)
    │   ├── creation (aggregate hashes from Series stores + book checkpoints)
    │   ├── recovery (resume_series, resume_book_in_series, start_new_book_in_series)
    │   ├── canonical serialization + fingerprint
    │   └── namespace isolation (series_id in path)
    │
    ├── SeriesMemoryStore (Source: series_memory_hash)
    ├── SeriesEntityRegistry (Source: series_entity_registry_hash)
    ├── SeriesGlossary (Source: series_glossary_hash)
    ├── SeriesKnowledge (Source: series_knowledge_hash)
    ├── SeriesManifest (Source: manifest_fingerprint, Authority for series_checkpoint_hash)
    │
    ├── Book Memory/Context (Source: book_memory_hash, book_context_hash)
    │   └── Existing per-book JSON files (validated by hash)
    │
    ├── Runtime Checkpoint (Source: session checkpoint refs)
    │   └── core/runtime_checkpoint/ (FROZEN — read-only reference)
    │
    ├── Production Runtime Checkpoint (Reference only)
    │   └── core/production_runtime/checkpoint.py (FROZEN — read-only reference)
    │
    └── Translation Session Checkpoint (Reference only)
        └── core/translation_session/session_checkpoint.py (FROZEN — read-only reference)
```

**Forbidden:** Bidirectional dependency `SeriesCheckpointManager ↔` frozen checkpoint modules internals

### 4.3 Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| `hashlib`, `json`, `dataclasses`, `datetime`, `pathlib`, `typing` | Stdlib | No external deps |
| `core.series_identity` | Internal | `SeriesManifest`, `SeriesRegistry`, `get_series_dir()` |
| `core.series_memory` | Internal | `SeriesMemoryStore`, `series_memory_hash` |
| `core.series_entity_registry` | Internal | `SeriesEntityRegistry`, `series_entity_registry_hash` |
| `core.glossary_builder` | Internal | `SeriesGlossary`, `glossary_hash` |
| `core.knowledge_runtime.loader` | Internal | `load_series_knowledge`, `SeriesKnowledge`, `knowledge_hash` |
| `core.runtime_checkpoint.models` | Internal (FROZEN) | `ProgressState`, `RequestManifest`, `CheckpointSnapshot` — **read-only reference** |
| `core.character_memory_v2.persistence` | Internal | `get_memory_file_path()` for book memory hash |
| `core.context_scene_memory.persistence` | Internal | `get_context_file_path()` for book context hash |

**No dependencies on:** `core.book_intake`, `core.translation_runtime`, `core.translation_pipeline`, `core.production_runtime` (except checkpoint reference), `core.runtime_orchestrator`

---

## 5. Data Models

### 5.1 SeriesCheckpoint (in `models.py`)

```python
@dataclass(frozen=True)
class SeriesCheckpoint:
    """Series-level recovery checkpoint with full hierarchy integrity."""
    schema_name: str                         # "ntpe.series_checkpoint"
    schema_version: str                      # "1.0"
    series_id: str                           # From SeriesManifest
    checkpoint_id: str                       # scheck_{sha256(series_id|timestamp)[:12]}
    created_at: str                          # ISO timestamp
    series_memory_hash: str                  # Hash of SeriesMemoryStore
    series_entity_registry_hash: str         # Hash of SeriesEntityRegistry
    series_glossary_hash: str                # Hash of SeriesGlossary
    series_knowledge_hash: str               # Hash of SeriesKnowledge
    manifest_fingerprint: str                # Hash of SeriesManifest
    book_checkpoints: tuple[BookCheckpointRef, ...]
    state_hash: str                          # SHA-256 of all above (integrity)

    def to_dict(self, include_state_hash: bool = True) -> dict[str, Any]:
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeriesCheckpoint":
        ...

    def get_checkpoint_hash(self) -> str:
        """Return state_hash for manifest integration."""
        return self.state_hash
```

### 5.2 BookCheckpointRef (in `models.py`)

```python
@dataclass(frozen=True)
class BookCheckpointRef:
    """Reference to a book's checkpoint state within Series."""
    book_identity: str
    volume_number: int
    book_memory_hash: str                    # Hash of character_memory_{book_identity}.json
    book_context_hash: str                   # Hash of context_scene_memory_{book_identity}.json
    latest_session_checkpoint_id: str | None # Most recent session checkpoint ID
    status: str                              # "in_progress" | "completed" | "promoted"

    def to_dict(self) -> dict[str, Any]:
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BookCheckpointRef":
        ...
```

### 5.3 SessionCheckpointRef (in `models.py`)

```python
@dataclass(frozen=True)
class SessionCheckpointRef:
    """Reference to a session's checkpoint within a Book."""
    session_id: str
    chunk_index: int
    progress: ProgressState                  # From core.runtime_checkpoint.models
    context_memory_hash: str                 # Hash of context state at this point
    request_manifest: RequestManifest | None # From core.runtime_checkpoint.models

    def to_dict(self) -> dict[str, Any]:
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionCheckpointRef":
        ...
```

### 5.4 Report Models (in `models.py`)

```python
@dataclass(frozen=True)
class CheckpointCreationReport:
    series_id: str
    checkpoint_id: str
    created_at: str
    state_hash: str
    book_checkpoints_count: int
    session_checkpoints_total: int
    manifest_fingerprint: str

@dataclass(frozen=True)
class SeriesResumeReport:
    series_id: str
    series_checkpoint_id: str
    series_manifest: SeriesManifest
    books_to_resume: list[BookResumeInfo]
    next_actions: list[str]

@dataclass(frozen=True)
class BookResumeInfo:
    volume_number: int
    book_identity: str
    book_status: str
    latest_session_id: str | None
    next_chunk_index: int
    hydration_required: bool

@dataclass(frozen=True)
class BookResumeReport:
    series_id: str
    book_identity: str
    volume_number: int
    book_memory_hash: str
    book_context_hash: str
    session_checkpoint: SessionCheckpointRef | None
    next_chunk_index: int
    hydration_summary: HydrationReport | None  # From series_memory.models

@dataclass(frozen=True)
class BookStartReport:
    series_id: str
    book_identity: str
    volume_number: int
    book_manifest: BookIntakeManifest  # From book_intake
    hydration_summary: HydrationReport
    book_checkpoint_ref: BookCheckpointRef
```

### 5.5 Validation Exceptions (in `validation.py`)

```python
class SeriesCheckpointValidationError(Exception):
    """Raised when SeriesCheckpoint schema validation fails."""
    pass

class SeriesCheckpointIntegrityError(Exception):
    """Raised when SeriesCheckpoint fingerprint verification fails (fail-closed)."""
    def __init__(self, checkpoint_id: str, detail: str):
        super().__init__(f"Integrity check failed for checkpoint {checkpoint_id}: {detail}")
        self.checkpoint_id = checkpoint_id

class SeriesCheckpointBookHashMismatchError(Exception):
    """Raised when book memory/context hash doesn't match actual file."""
    pass

class SeriesCheckpointSessionMismatchError(Exception):
    """Raised when session checkpoint reference doesn't match."""
    pass
```

---

## 6. Series Checkpoint Identity Semantics

### 6.1 Namespace Isolation

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_checkpoint_{series_id}.json` |
| **Manifest Key** | All operations require explicit `series_id` |
| **Creation** | Only checkpoint matching `series_id` created |
| **Book References** | Book identity validated against SeriesManifest |
| **Session References** | Session ID validated against runtime checkpoint store |
| **Load Validation** | Payload `series_id` must match directory name |

### 6.2 Checkpoint ID Format

| Level | ID Format | Example |
|-------|-----------|---------|
| Series | `scheck_{sha256(series_id|timestamp)[:12]}` | `scheck_a1b2c3d4e5f6` |
| Book | Uses existing `book_identity` (Stage 4 frozen) | `b1o2k3i4d5e6n7t8` |
| Session | Uses existing `session_id` (RM-6.3.2) | `sess_a1b2c3d4e5f6` |
| Chunk | Integer index within session | `0, 1, 2...` |

---

## 7. Serialization Rules

### 7.1 Canonical JSON

```python
def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

### 7.2 Series Checkpoint Fingerprint

```python
def compute_series_checkpoint_fingerprint(series_checkpoint_dict: dict) -> str:
    """Compute SHA-256 of canonical checkpoint payload (excluding state_hash itself)."""
    payload = {k: v for k, v in series_checkpoint_dict.items() if k != "state_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 7.3 Round-Trip Guarantee

```
series_checkpoint → to_canonical_json → bytes → sha256 → state_hash
series_checkpoint → to_dict() → load → serialize → same state_hash
```

**Deterministic:** Same inputs → bit-for-bit identical JSON → identical fingerprint.

---

## 8. Validation Rules

### 8.1 Schema Validation (on Load)

| Check | Fail Behavior |
|-------|---------------|
| `schema_name` == "ntpe.series_checkpoint" | `SeriesCheckpointValidationError` |
| `schema_version` == "1.0" | `SeriesCheckpointValidationError` |
| `series_id` matches directory/filename | `SeriesCheckpointValidationError` |
| `state_hash` matches computed | `SeriesCheckpointIntegrityError` (fail-closed) |
| `book_checkpoints` is list of valid BookCheckpointRef | `SeriesCheckpointValidationError` |
| Each `BookCheckpointRef` has valid `status` enum | `SeriesCheckpointValidationError` |
| Each `SessionCheckpointRef` has valid `ProgressState` | `SeriesCheckpointValidationError` |

### 8.2 Business Rule Validation (on Creation/Recovery)

| Operation | Validation |
|-----------|------------|
| `create_checkpoint()` | All Series stores must have matching `series_id` |
| `create_checkpoint()` | All referenced books must exist in SeriesManifest |
| `create_checkpoint()` | Book memory/context hashes must match actual files |
| `create_checkpoint()` | Session checkpoint IDs must exist in runtime checkpoint store |
| `resume_series()` | SeriesCheckpoint state_hash must match |
| `resume_series()` | All book memory/context hashes must match |
| `resume_book_in_series()` | BookCheckpointRef must exist in SeriesCheckpoint |
| `resume_book_in_series()` | Book memory/context hashes must match |
| `start_new_book_in_series()` | volume_number must be sequential |

### 8.3 Fail-Closed Principle

- **Any validation failure → Exception**, no partial load, no fallback defaults
- Corrupted checkpoint file → `SeriesCheckpointIntegrityError` → operation blocked
- Book/session hash mismatch → `SeriesCheckpointBookHashMismatchError` / `SeriesCheckpointSessionMismatchError` → operation blocked
- No silent data corruption

---

## 9. SeriesCheckpointManager (in `manager.py`)

### 9.1 Core Methods

```python
class SeriesCheckpointManager:
    """Orchestrate Series checkpoint creation, persistence, and recovery."""

    version = "p0-stage5-batch5.6"

    def __init__(
        self,
        output_root: Path,
        series_registry: SeriesRegistry,
        series_memory_store: SeriesMemoryStore,
        series_entity_registry: SeriesEntityRegistry,
        series_glossary: SeriesGlossary,
        series_knowledge: SeriesKnowledge,
    ):
        self.output_root = output_root
        self.series_registry = series_registry
        self.series_memory_store = series_memory_store
        self.series_entity_registry = series_entity_registry
        self.series_glossary = series_glossary
        self.series_knowledge = series_knowledge

    def create_checkpoint(
        self,
        series_id: str,
        include_completed_books: bool = True,
    ) -> CheckpointCreationReport:
        """
        Create a new SeriesCheckpoint aggregating all current state.

        Called after:
        - Book promotion completed (series memory/glossary/knowledge updated)
        - Manual series-level save requested
        """
        ...

    def save_checkpoint(self, checkpoint: SeriesCheckpoint) -> Path:
        """Persist SeriesCheckpoint to disk with atomic write."""
        ...

    def load_latest_checkpoint(self, series_id: str) -> SeriesCheckpoint | None:
        """Load latest SeriesCheckpoint for series, or None if not found."""
        ...

    def validate_checkpoint(self, checkpoint: SeriesCheckpoint) -> None:
        """Validate all hashes in checkpoint against actual files (fail-closed)."""
        ...
```

### 9.2 Recovery Methods (in `recovery.py`)

```python
def resume_series(
    series_id: str,
    output_root: Path,
    series_registry: SeriesRegistry,
    series_memory_store: SeriesMemoryStore,
    series_entity_registry: SeriesEntityRegistry,
    series_glossary: SeriesGlossary,
    series_knowledge: SeriesKnowledge,
) -> SeriesResumeReport:
    """
    Resume entire series from latest SeriesCheckpoint.
    """
    ...

def resume_book_in_series(
    series_id: str,
    book_identity: str,
    output_root: Path,
    series_registry: SeriesRegistry,
    series_memory_store: SeriesMemoryStore,
    series_entity_registry: SeriesEntityRegistry,
    series_glossary: SeriesGlossary,
    series_knowledge: SeriesKnowledge,
) -> BookResumeReport:
    """
    Resume a specific book within a series.
    """
    ...

def start_new_book_in_series(
    series_id: str,
    book_identity: str,
    volume_number: int,
    source_path: Path,
    output_root: Path,
    series_registry: SeriesRegistry,
    series_memory_store: SeriesMemoryStore,
    series_entity_registry: SeriesEntityRegistry,
    series_glossary: SeriesGlossary,
    series_knowledge: SeriesKnowledge,
) -> BookStartReport:
    """
    Start a fresh book in an existing series.
    """
    ...
```

---

## 10. Persistence Helpers (in `persistence.py`)

### 10.1 File Path

```python
def get_series_checkpoint_path(output_root: Path, series_id: str) -> Path:
    """Get the path for series checkpoint file."""
    series_dir = output_root / "series" / series_id
    return series_dir / f"series_checkpoint_{series_id}.json"
```

### 10.2 Save

```python
def save_series_checkpoint(series_checkpoint: SeriesCheckpoint, path: Path) -> None:
    """Save SeriesCheckpoint to disk with atomic write and fingerprint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    data = series_checkpoint.to_dict(include_state_hash=True)
    temp_path.write_text(
        to_canonical_json(data),
        encoding="utf-8"
    )
    temp_path.replace(path)
```

### 10.3 Load

```python
def load_series_checkpoint_from_path(path: Path, expected_series_id: str) -> SeriesCheckpoint:
    """Load SeriesCheckpoint from disk with integrity verification (fail-closed)."""
    if not path.exists():
        return None  # Fresh series

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SeriesCheckpointValidationError(f"Invalid JSON in checkpoint file: {e}")

    # Schema validation
    if data.get("schema_name") != "ntpe.series_checkpoint":
        raise SeriesCheckpointValidationError(f"Invalid schema_name: {data.get('schema_name')}")
    if data.get("schema_version") != "1.0":
        raise SeriesCheckpointValidationError(f"Invalid schema_version: {data.get('schema_version')}")
    if data.get("series_id") != expected_series_id:
        raise SeriesCheckpointValidationError(f"Series ID mismatch: expected {expected_series_id}, got {data.get('series_id')}")

    # Fingerprint verification (fail-closed)
    stored_hash = data.get("state_hash", "")
    if stored_hash:
        computed_hash = compute_series_checkpoint_fingerprint(data)
        if stored_hash != computed_hash:
            raise SeriesCheckpointIntegrityError(data.get("checkpoint_id", "unknown"), f"Checkpoint fingerprint mismatch: stored={stored_hash}, computed={computed_hash}")

    # Reconstruct nested objects
    book_checkpoints = tuple(BookCheckpointRef.from_dict(b) for b in data.get("book_checkpoints", []))

    return SeriesCheckpoint(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        checkpoint_id=data["checkpoint_id"],
        created_at=data["created_at"],
        series_memory_hash=data["series_memory_hash"],
        series_entity_registry_hash=data["series_entity_registry_hash"],
        series_glossary_hash=data["series_glossary_hash"],
        series_knowledge_hash=data["series_knowledge_hash"],
        manifest_fingerprint=data["manifest_fingerprint"],
        book_checkpoints=book_checkpoints,
        state_hash=stored_hash,
    )


def load_latest_series_checkpoint(series_id: str, output_root: Path) -> SeriesCheckpoint | None:
    """Load latest SeriesCheckpoint from output root."""
    path = get_series_checkpoint_path(output_root, series_id)
    return load_series_checkpoint_from_path(path, series_id)
```

---

## 11. Manifest Integration

### 11.1 Existing Infrastructure (Already Implemented)

`SeriesManifest` already has `series_checkpoint_hash: str = field(default="")` (line 105).
`SeriesManifest.with_series_checkpoint_hash()` already exists (lines 260-276).
`SeriesRegistry.update_series_checkpoint_hash()` already exists (lines 342-353).

### 11.2 Batch 5.6 Responsibility

After `SeriesCheckpointManager.create_checkpoint()` successfully saves the checkpoint:

```python
# In SeriesCheckpointManager.create_checkpoint()
# ... after save_checkpoint(checkpoint) ...
# Update manifest
self.series_registry.update_series_checkpoint_hash(series_id, checkpoint.state_hash)
```

### 11.3 Derived-State Boundary (Explicit Contract)

| Property | Requirement |
|----------|-------------|
| **Derived** | `series_checkpoint_hash` computed FROM SeriesCheckpoint, never reverse |
| **Read-Only from Checkpoint** | Checkpoint computes hash; Manifest stores it. Checkpoint never reads this field for authority. |
| **Never Authority Source** | Manifest field is a fingerprint only. Does not control checkpoint content. |
| **Never Overwrites SeriesIdentity** | `series_id`, `series_name`, `created_at` remain Manifest authority. |
| **Never Overwrites Canonical State** | Checkpoint owns hashes. Manifest hash is a checksum only. |

---

## 12. Cross-Series Isolation (Hard Enforcement)

### 12.1 Namespace Isolation Rules

| Layer | Mechanism |
|-------|-----------|
| **File Path** | `output/series/{series_id}/series_checkpoint_{series_id}.json` |
| **Manifest Key** | All queries require explicit `series_id` |
| **Creation** | Only checkpoint matching `series_id` created |
| **Book References** | Book identity validated against SeriesManifest |
| **Session References** | Session ID validated against runtime checkpoint store |
| **Load Validation** | Payload `series_id` must match directory name |

### 12.2 Hard Failure Cases (All MUST Fail)

| Case | Validation Point |
|------|------------------|
| Load checkpoint with mismatched `series_id` | `load_series_checkpoint_from_path()` |
| Create checkpoint for wrong series | `create_checkpoint()` |
| Book reference not in SeriesManifest | `create_checkpoint()` |
| Book memory hash mismatch | `validate_checkpoint()` |
| Book context hash mismatch | `validate_checkpoint()` |
| Session checkpoint not found | `validate_checkpoint()` |
| Session state_hash mismatch | `validate_checkpoint()` |
| File path collision | Impossible — directory隔离 |

---

## 13. CSI-05 Acceptance Tests (Hard Gates)

> **All MUST PASS. Any failure → Batch 5.6 not accepted.**

| Test ID | Description | Verification |
|---------|-------------|--------------|
| **CSI-05** | Series A checkpoint ≠ Series B | Verify file naming `series_checkpoint_{series_id}.json` and manifest hash isolation |
| **SC-01** | Series checkpoint creation with all hashes | Checkpoint saved, state_hash valid |
| **SC-02** | 4-level hierarchy present | Series → Book → Session → Chunk refs |
| **SC-03** | Series-level recovery | All Series stores restored, books resumable |
| **SC-04** | Book-in-Series recovery | Book hydrated, session restored, chunk progress correct |
| **SC-05** | Hash integrity: corrupt any hash → exception | `SeriesCheckpointIntegrityError` raised |
| **SC-06** | Checkpoint idempotent | Save twice → same state_hash |
| **SC-07** | Persistence round-trip | Save → load → all hashes match |
| **SC-08** | Cross-series isolation | Series A checkpoint not in Series B |
| **SC-09** | Manifest hash integration | `series_checkpoint_hash` present, updates on checkpoint change |
| **SC-10** | Backward compat: old manifest loads | Empty string default |
| **SC-11** | Provider/Network/Translation = 0/0/0 | Verified in test runs |
| **SC-12** | Root hygiene: no files in repo root | Git status clean |
| **SC-13** | Frozen contract isolation | runtime_checkpoint, production_runtime, translation_session unchanged |
| **SC-14** | Book checkpoint hash sync | Book memory/context hash matches actual files |
| **SC-15** | Session checkpoint integration | SessionCheckpointRef correctly references runtime_checkpoint |

---

## 14. Frozen Contracts Audit

**Batch 5.6 MUST NOT modify (to be verified):**

| Frozen Contract | Status |
|-----------------|--------|
| Runtime Contract | No touch |
| Context Pipeline Contract | No touch |
| Prompt Pipeline Contract | No touch |
| Plugin Contract | No touch |
| Production Pipeline Contract | No touch |
| Translation Runtime Contract | No touch |
| Intelligence Contract | No touch |
| Knowledge Contract | No touch |
| Snapshot Contract | No touch |
| Character Memory v2 core | No touch |
| Context/Scene Memory core | No touch |
| Entity Resolver core | No touch |
| **Runtime Checkpoint core** | **FROZEN** — models, manager, validator unchanged |
| **Production Runtime Checkpoint** | **FROZEN** — no modifications |
| **Translation Session Checkpoint** | **FROZEN** — no modifications |
| All 9 Foundation Frozen Contracts | No touch |

**New Contract Created by Batch 5.6:**
- **Series Checkpoint Contract** (`core/series_checkpoint/`) — to be added to Foundation Manifest in Batch 5.9

---

## 15. Forbidden Modifications (Enforced)

| Category | Forbidden |
|----------|-----------|
| `core/runtime_checkpoint/` | **FROZEN** |
| `core/production_runtime/checkpoint.py` | **FROZEN** |
| `core/translation_session/session_checkpoint.py` | **FROZEN** |
| `core/series_identity/manifest.py` | **FROZEN** (field exists, only call registry method) |
| `core/series_identity/registry.py` | **FROZEN** (method exists, only call it) |
| `core/character_memory_v2/` | **FROZEN** |
| `core/context_scene_memory/` | **FROZEN** |
| `core/book_intake/` | **FROZEN** |
| `core/translation_runtime/` | **FROZEN** |
| `core/translation_pipeline/` | **FROZEN** |
| `core/production_runtime/` (except checkpoint reference) | **FROZEN** |
| Any Frozen Contract (9 existing) | **FROZEN** |
| Feature flag changes | **FROZEN** |
| TXT/EPUB/Translation behavior | **FROZEN** |
| Provider/Network/Translation execution | **FROZEN** |

---

## 16. Test Requirements

### 16.1 Unit Tests (Minimum)

| Test | Description |
|------|-------------|
| `test_series_checkpoint_creation` | Create checkpoint with all hashes |
| `test_series_checkpoint_serialization_roundtrip` | Save → load → fingerprint matches |
| `test_series_checkpoint_fingerprint_integrity` | Tampered file → IntegrityError |
| `test_book_checkpoint_ref_validation` | Book memory/context hash matches files |
| `test_session_checkpoint_ref_validation` | Session checkpoint ID exists and hash matches |
| `test_create_checkpoint_aggregates_all` | Manager aggregates Series stores + book refs |
| `test_validate_checkpoint_fail_closed` | Any hash mismatch → exception |
| `test_resume_series_restores_all` | Full series restore from checkpoint |
| `test_resume_book_in_series` | Book resume with hydration + session |
| `test_start_new_book_in_series` | Fresh book with series hydration |
| `test_namespace_isolation` | Series A checkpoint not in Series B |
| `test_persistence_roundtrip` | Save → load → fingerprint matches |
| `test_persistence_corrupted_fail_closed` | Corrupted file → IntegrityError |
| `test_deterministic_serialization` | Same checkpoint → bit-for-bit identical JSON |
| `test_manifest_hash_integration` | Checkpoint hash stored in SeriesManifest |
| `test_manifest_hash_updates` | Manifest fingerprint changes with checkpoint |
| `test_old_manifest_loads` | Pre-Batch 5.6 manifest loads with empty hash |

### 16.2 Property-Based Tests

| Test | Iterations |
|------|------------|
| `test_series_checkpoint_fingerprint_deterministic` | 1000 |
| `test_serialization_roundtrip_property` | 1000 |
| `test_checkpoint_creation_deterministic` | 1000 |

### 16.3 Cross-Series Isolation Tests (CSI-05)

| Test | CSI Mapping |
|------|-------------|
| `test_csi_05_checkpoint_file_isolation` | CSI-05 |
| `test_csi_05_resume_isolation` | CSI-05 |

### 16.4 Integration Tests

| Test | Description |
|------|-------------|
| `test_series_checkpoint_in_multi_book_translation` | Book 1 promote → checkpoint → Book 2 resume |
| `test_cross_series_no_leakage_checkpoint` | Series A checkpoint not in Series B resume |
| `test_full_series_resume_after_restart` | Process restart simulation |

---

## 17. Batch 5.6 Acceptance Test Matrix (Comprehensive)

| Category | Test | Description | Pass Criteria |
|----------|------|-------------|---------------|
| **Persistence** | `test_persist_save_load` | Save checkpoint, load, verify fingerprint | Fingerprint matches, structure intact |
| **Persistence** | `test_persist_corrupted_fail_closed` | Corrupt JSON, attempt load | `SeriesCheckpointIntegrityError` raised |
| **Persistence** | `test_persist_missing_file` | Load non-existent checkpoint | Returns None |
| **Persistence** | `test_persist_restart` | Process restart simulation | Reload produces identical state |
| **Reload** | `test_reload_idempotent` | Load → save → load → save | Bit-for-bit identical JSON |
| **Hierarchy** | `test_4level_hierarchy` | Series → Book → Session → Chunk | All levels present with valid refs |
| **Hierarchy** | `test_book_refs_match_manifest` | BookCheckpointRef books match SeriesManifest | All books accounted for |
| **Hierarchy** | `test_session_refs_exist` | SessionCheckpointRef IDs exist in runtime store | No dangling refs |
| **Recovery** | `test_resume_series` | Full series resume | All stores restored, books resumable |
| **Recovery** | `test_resume_book_in_series` | Single book resume | Hydration + session restore |
| **Recovery** | `test_start_new_book` | Fresh book in existing series | Hydration + BookCheckpointRef created |
| **Corruption** | `test_corruption_state_hash` | Tamper state_hash | IntegrityError on load |
| **Corruption** | `test_corruption_book_hash` | Tamper book_memory_hash | BookHashMismatchError on validate |
| **Corruption** | `test_corruption_session_hash` | Tamper session state_hash | SessionMismatchError on validate |
| **Corruption** | `test_corruption_json` | Malformed JSON | ValidationError on load |
| **Corruption** | `test_corruption_schema` | Wrong schema_name/version | ValidationError on load |
| **Deterministic** | `test_deterministic_json` | Same checkpoint, multiple serializations | Bit-for-bit identical |
| **Deterministic** | `test_deterministic_hash` | Same checkpoint, multiple hashes | Identical SHA-256 |
| **Backward Compat** | `test_compat_no_checkpoint` | Series without checkpoint works | Works identically to baseline |
| **Fail-Closed** | `test_fail_closed_all_paths` | All validation paths throw exceptions | No fallback defaults |

---

## 18. Validation Gates

**All must PASS before Batch 5.6 considered complete:**

- [ ] `python ntpe_validate.py` — PASS (no new warnings)
- [ ] `python -m compileall core/` — 0 errors
- [ ] `git diff --check` — clean
- [ ] All unit tests PASS
- [ ] All property-based tests PASS (1000 iterations each)
- [ ] All CSI-05 + SC-01~15 tests PASS
- [ ] Batch 5.6 Acceptance Test Matrix (§17) all PASS
- [ ] No regression in existing pytest tests (Series Identity, Series Memory, Series Entity, Series Glossary, Series Knowledge, Runtime Checkpoint)
- [ ] Provider = 0, Network = 0, Translation = 0 (verified in test runs)

---

## 19. Git Scope Rules

**Allowed Changes:**

- **NEW** `core/series_checkpoint/` (complete module: `__init__.py`, `models.py`, `manager.py`, `persistence.py`, `recovery.py`, `validation.py`)
- **ADDITIVE** `core/series_identity/registry.py` — **CALL ONLY** `update_series_checkpoint_hash()` (method already exists)
- **NEW** `tests/series/test_batch5_6_*.py` (test files)

**Forbidden:**

- Any modification to existing production code outside allowed additive calls
- Any modification to Frozen Contracts
- Any commit/push/tag (deliverables only)

---

## 20. Delivery Rules

**Deliverables (working tree changes only, no staging):**

1. New `core/series_checkpoint/__init__.py`
2. New `core/series_checkpoint/models.py`
3. New `core/series_checkpoint/manager.py`
4. New `core/series_checkpoint/persistence.py`
5. New `core/series_checkpoint/recovery.py`
6. New `core/series_checkpoint/validation.py`
7. Additive call to `SeriesRegistry.update_series_checkpoint_hash()` in `SeriesCheckpointManager.create_checkpoint()`
8. `tests/series/test_batch5_6_*.py`
9. This Implementation Task document (as record)

**No staging, no commit, no push, no tag.**

---

## 21. Rollback Boundary

**Clean Rollback:**

- Delete `core/series_checkpoint/` directory
- Remove call to `update_series_checkpoint_hash()` from `SeriesCheckpointManager.create_checkpoint()`
- Delete `tests/series/test_batch5_6_*.py`

- No other files modified
- No database/migrations
- No configuration changes
- No side effects on existing modules
- **Frozen checkpoint files UNCHANGED — no revert needed**

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
- `core/series_checkpoint/` — implementation
- `tests/series/` — tests
- `docs/governance/rm8/` — docs
- `artifacts/` — diagnostic output only

---

## 24. Completion Criteria

**Batch 5.6 Complete When:**

1. All §16 unit tests PASS
2. All §16 property-based tests PASS (1000 iterations each)
3. All §16 CSI-05 + SC-01~15 tests PASS
4. All §17 Batch 5.6 Acceptance Test Matrix PASS
5. Validation gates (§18) all PASS
6. Git status shows only allowed new files + allowed additive call
7. No production code modified outside allowed additive call
8. No Frozen Contracts modified
9. **Frozen checkpoint modules unchanged** (runtime_checkpoint, production_runtime/checkpoint, translation_session/session_checkpoint)

**Status Report:** "P0 Stage 5 Batch 5.6 Specification READY — Implementation COMPLETE — Awaiting Owner Review"

---

## 25. Sign-Off

| Role | Confirmation | Date |
|------|--------------|------|
| Spec Author | Preflight complete, models defined, integration points specified, all decisions frozen | 2026-08-21 |
| Owner | Authorization to proceed | ____________ |
| QA | CSI-05 + SC-01~15 test matrix & Acceptance Test Matrix accepted | ____________ |

---

## 26. Owner Decisions — NONE REQUIRED

All architectural decisions for Batch 5.6 are **FROZEN** via P0 Stage 5 Formal Specification (§29, D-01 ~ D-10):

| Decision | FROZEN Choice |
|----------|---------------|
| Checkpoint Hierarchy Scope | 4-level hierarchy (Series/Book/Session/Chunk) |
| Checkpoint Trigger Policy | Automatic on book promotion + manual option |
| Recovery Granularity | Both series-level and book-in-series recovery |
| Frozen Checkpoint Integration | Reference existing (runtime_checkpoint, production, session) |
| Manifest Hash | Use existing `series_checkpoint_hash` field |
| Cross-Series Isolation | Directory + filename + manifest hash + ID validation |

**OWNER DECISION REQUIRED: NONE**

---

*End of Batch 5.6 Implementation Task. Specification COMPLETE — All decisions frozen — READY FOR OWNER AUTHORIZATION.*
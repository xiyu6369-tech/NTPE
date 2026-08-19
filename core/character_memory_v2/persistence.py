"""Character Memory v2 Persistence Layer.

Provides deterministic, fail-closed loading and saving of MemoryStore
for per-book persistence across translation sessions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional

from .models import SCHEMA_VERSION, FactType, ApprovalMetadata
from .serialization import deserialize_memory_store, serialize_memory_store
from .store import (
    MemoryStore,
    add_or_merge_memory,
    create_evidence,
    create_memory,
    default_expiry_for_fact,
)
from .validation import CharacterMemoryValidationError

# Series Memory integration (additive, optional)
try:
    from core.series_memory import (
        SeriesMemoryStore,
        hydrate_book_store,
    )
    from core.series_memory.persistence import load_series_memory
    _SERIES_MEMORY_AVAILABLE = True
except ImportError:
    _SERIES_MEMORY_AVAILABLE = False
    SeriesMemoryStore = None  # type: ignore
    hydrate_book_store = None  # type: ignore
    load_series_memory = None  # type: ignore


def compute_book_identity(input_path: Path, project_name: str) -> str:
    """Compute deterministic book identity from source file and project.

    Uses source file path and project name to create a stable identifier
    that matches NTPE's deterministic source identity principles.
    """
    identity_source = f"{project_name}|{input_path.resolve()}"
    return hashlib.sha256(identity_source.encode("utf-8")).hexdigest()[:16]


def get_memory_file_path(output_dir: Path, book_identity: str) -> Path:
    """Get the memory persistence file path for a given book.

    Stored alongside translation output per Artifact Isolation.
    """
    return output_dir / f"character_memory_{book_identity}.json"


def save_character_memory(store: MemoryStore, memory_file: Path) -> dict[str, Any]:
    """Save MemoryStore to disk with validation.

    Returns metadata including file hash and snapshot version.
    """
    serialized = serialize_memory_store(store)
    memory_file.write_text(serialized, encoding="utf-8", newline="\n")

    file_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return {
        "file_hash": file_hash,
        "snapshot_version": store.snapshot_version,
        "schema_version": SCHEMA_VERSION,
    }


def load_character_memory(memory_file: Path) -> MemoryStore:
    """Load MemoryStore from disk with fail-closed validation.

    Raises CharacterMemoryValidationError on any corruption or schema mismatch.
    """
    if not memory_file.exists():
        raise CharacterMemoryValidationError(f"memory file not found: {memory_file}")

    content = memory_file.read_bytes()
    if not content:
        raise CharacterMemoryValidationError(f"memory file is empty: {memory_file}")

    try:
        return deserialize_memory_store(content)
    except CharacterMemoryValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CharacterMemoryValidationError(
            f"memory file is not valid UTF-8 JSON: {memory_file}"
        ) from exc


def verify_memory_integrity(memory_file: Path, expected_hash: str) -> bool:
    """Verify memory file matches expected hash.

    Returns True if hash matches, False otherwise.
    """
    if not memory_file.exists():
        return False
    content = memory_file.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    return actual_hash == expected_hash


def migrate_lts_to_v2(lts_path: Path, output_dir: Path, book_identity: str) -> tuple[MemoryStore, dict[str, Any]]:
    """Migrate LTS character memory JSON to v2 MemoryStore.

    Deterministic, loss-aware, fail-closed migration.
    Preserves original LTS file.

    Returns:
        (MemoryStore, migration_report)
    """
    if not lts_path.exists():
        raise CharacterMemoryValidationError(f"LTS memory file not found: {lts_path}")

    content = lts_path.read_text(encoding="utf-8")
    try:
        lts_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise CharacterMemoryValidationError(f"LTS memory file is not valid JSON: {lts_path}") from exc

    characters = lts_data.get("characters", {})
    if not isinstance(characters, dict) or not characters:
        raise CharacterMemoryValidationError("LTS memory 'characters' must be a non-empty object")

    store = MemoryStore()
    migrated = 0
    skipped = 0
    errors = []

    for korean, chinese in characters.items():
        if not isinstance(korean, str) or not isinstance(chinese, str):
            errors.append(f"Invalid entry type: {korean!r} -> {chinese!r}")
            skipped += 1
            continue
        korean = korean.strip()
        chinese = chinese.strip()
        if not korean or not chinese:
            errors.append(f"Empty key or value: {korean!r} -> {chinese!r}")
            skipped += 1
            continue

        try:
            # Generate deterministic character_id from Korean name (ASCII-safe)
            import hashlib
            korean_hash = hashlib.sha256(korean.encode("utf-8")).hexdigest()[:16]
            character_id = f"char_{korean_hash}"
            source_hash = hashlib.sha256(korean.encode("utf-8")).hexdigest()

            evidence = create_evidence(
                evidence_type="historical_import",
                source_case_id="lts_migration",
                source_segment_id="character_memory_lts",
                source_text_hash=source_hash,
                excerpt=korean,
                language="ko",
                observed_at="2026-01-01T00:00:00Z",
            )

            record = create_memory(
                character_id=character_id,
                fact_type="canonical_name",
                value=chinese,
                evidence=evidence,
                confidence=1.0,
                approval_status="approved",
                source_language="ko",
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
                expiry_policy=default_expiry_for_fact(FactType.CANONICAL_NAME),
                status="active",
                approval_metadata=ApprovalMetadata(
                    approved_value=chinese,
                    approved_at="2026-01-01T00:00:00Z",
                    reviewer="lts_migration",
                    decision_reference="lts_to_v2_migration",
                ),
            )

            result = add_or_merge_memory(store, record, now="2026-01-01T00:00:00Z")
            if result.disposition.value in ("accepted", "merged"):
                migrated += 1
            else:
                skipped += 1
                errors.append(f"Merge failed for {korean}: {result.message}")
        except Exception as exc:
            skipped += 1
            errors.append(f"Migration error for {korean}: {exc}")

    migration_report = {
        "lts_file": str(lts_path),
        "total_entries": len(characters),
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "success": skipped == 0 and len(errors) == 0,
    }

    if not migration_report["success"]:
        raise CharacterMemoryValidationError(
            f"LTS migration had {skipped} skipped entries and {len(errors)} errors"
        )

    memory_file = get_memory_file_path(output_dir, book_identity)
    metadata = save_character_memory(store, memory_file)

    return store, migration_report


def load_or_create_character_memory(
    *,
    output_dir: Path,
    input_path: Path,
    project_name: str,
    lts_path: Path | None = None,
    series_id: Optional[str] = None,
    series_memory_hash: Optional[str] = None,
) -> tuple[MemoryStore, dict[str, Any]]:
    """Load existing memory, migrate from LTS, or create new.

    Priority:
    1. Existing v2 memory file
    2. LTS migration
    3. Fresh MemoryStore

    If series_id and series_memory_hash are provided, hydrate from SeriesMemoryStore.

    Returns:
        (MemoryStore, load_report)
    """
    book_identity = compute_book_identity(input_path, project_name)
    memory_file = get_memory_file_path(output_dir, book_identity)

    load_report = {
        "book_identity": book_identity,
        "memory_file": str(memory_file),
        "source": "unknown",
        "migration_report": None,
        "hydration_report": None,
    }

    if memory_file.exists():
        try:
            store = load_character_memory(memory_file)
            load_report["source"] = "v2_persisted"
            # Hydrate from SeriesMemoryStore if series_id provided
            if series_id and series_memory_hash and _SERIES_MEMORY_AVAILABLE:
                series_store = SeriesMemoryStore(series_id=series_id)  # type: ignore[operator]
                series_dir = output_dir / "series" / series_id
                series_memory_file = series_dir / f"series_memory_{series_id}.json"
                if series_memory_file.exists():
                    series_mapping, _ = load_series_memory(series_memory_file)  # type: ignore[operator]
                    series_store.mapping = series_mapping
                    series_store._series_memory_hash = series_memory_hash
                    hydration_report = hydrate_book_store(  # type: ignore[operator]
                        series_store=series_store,
                        book_store=store,
                        book_identity=book_identity,
                        series_memory_hash=series_memory_hash,
                    )
                    load_report["hydration_report"] = hydration_report.to_dict()
            return store, load_report
        except CharacterMemoryValidationError as exc:
            raise CharacterMemoryValidationError(
                f"Failed to load existing memory file {memory_file}: {exc}"
            ) from exc

    if lts_path and lts_path.exists():
        try:
            store, migration_report = migrate_lts_to_v2(lts_path, output_dir, book_identity)
            load_report["source"] = "lts_migration"
            load_report["migration_report"] = migration_report
            # Hydrate from SeriesMemoryStore if series_id provided
            if series_id and series_memory_hash and _SERIES_MEMORY_AVAILABLE:
                series_store = SeriesMemoryStore(series_id=series_id)  # type: ignore[operator]
                series_dir = output_dir / "series" / series_id
                series_memory_file = series_dir / f"series_memory_{series_id}.json"
                if series_memory_file.exists():
                    series_mapping, _ = load_series_memory(series_memory_file)  # type: ignore[operator]
                    series_store.mapping = series_mapping
                    series_store._series_memory_hash = series_memory_hash
                    hydration_report = hydrate_book_store(  # type: ignore[operator]
                        series_store=series_store,
                        book_store=store,
                        book_identity=book_identity,
                        series_memory_hash=series_memory_hash,
                    )
                    load_report["hydration_report"] = hydration_report.to_dict()
            return store, load_report
        except CharacterMemoryValidationError as exc:
            raise CharacterMemoryValidationError(
                f"LTS migration failed: {exc}"
            ) from exc

    store = MemoryStore()
    load_report["source"] = "fresh"
    # Hydrate from SeriesMemoryStore if series_id provided (for fresh store)
    if series_id and series_memory_hash and _SERIES_MEMORY_AVAILABLE:
        series_store = SeriesMemoryStore(series_id=series_id)  # type: ignore[operator]
        series_dir = output_dir / "series" / series_id
        series_memory_file = series_dir / f"series_memory_{series_id}.json"
        if series_memory_file.exists():
            series_mapping, _ = load_series_memory(series_memory_file)  # type: ignore[operator]
            series_store.mapping = series_mapping
            series_store._series_memory_hash = series_memory_hash
            hydration_report = hydrate_book_store(  # type: ignore[operator]
                series_store=series_store,
                book_store=store,
                book_identity=book_identity,
                series_memory_hash=series_memory_hash,
            )
            load_report["hydration_report"] = hydration_report.to_dict()
    return store, load_report


__all__ = [
    "compute_book_identity",
    "get_memory_file_path",
    "save_character_memory",
    "load_character_memory",
    "verify_memory_integrity",
    "migrate_lts_to_v2",
    "load_or_create_character_memory",
]
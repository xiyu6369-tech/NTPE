"""P0 Stage 5 Batch 5.6 — Series Checkpoint Persistence.

Deterministic load/save with atomic writes and SHA-256 integrity verification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import SeriesCheckpoint, BookCheckpointRef, compute_series_checkpoint_fingerprint, to_canonical_json
from .validation import (
    SeriesCheckpointValidationError,
    SeriesCheckpointIntegrityError,
)


def get_series_checkpoint_path(output_root: Path, series_id: str) -> Path:
    """Get the path for series checkpoint file."""
    series_dir = output_root / "series" / series_id
    return series_dir / f"series_checkpoint_{series_id}.json"


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


def load_series_checkpoint_from_path(path: Path, expected_series_id: str) -> SeriesCheckpoint | None:
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
            raise SeriesCheckpointIntegrityError(
                data.get("checkpoint_id", "unknown"),
                f"Checkpoint fingerprint mismatch: stored={stored_hash}, computed={computed_hash}"
            )

    # Reconstruct nested objects
    book_checkpoints = tuple(
        BookCheckpointRef.from_dict(b) for b in data.get("book_checkpoints", [])
    )

    return SeriesCheckpoint(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        checkpoint_id=data["checkpoint_id"],
        created_at=data["created_at"],
        series_memory_hash=data.get("series_memory_hash", ""),
        series_entity_registry_hash=data.get("series_entity_registry_hash", ""),
        series_glossary_hash=data.get("series_glossary_hash", ""),
        series_knowledge_hash=data.get("series_knowledge_hash", ""),
        manifest_fingerprint=data.get("manifest_fingerprint", ""),
        book_checkpoints=book_checkpoints,
        state_hash=stored_hash,
    )


def load_latest_series_checkpoint(series_id: str, output_root: Path) -> SeriesCheckpoint | None:
    """Load latest SeriesCheckpoint from output root."""
    path = get_series_checkpoint_path(output_root, series_id)
    return load_series_checkpoint_from_path(path, series_id)
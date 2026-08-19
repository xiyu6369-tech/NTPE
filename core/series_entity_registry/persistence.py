"""P0 Stage 5 Batch 5.3 — Series Entity Registry Persistence.

Deterministic canonical JSON serialization with SHA-256 fingerprint.
Fail-closed on corruption. Atomic writes via temp file + os.replace.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Tuple

from .models import (
    SeriesEntityRecord,
    EntityPromotionRecord,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from .validation import (
    compute_series_entity_registry_fingerprint,
    to_canonical_json,
    validate_series_entity_registry_payload,
    verify_series_entity_registry_fingerprint,
    SeriesEntityValidationError,
    SeriesEntityIntegrityError,
)


def get_series_dir(output_root: Path, series_id: str) -> Path:
    """Get the series directory path."""
    return output_root / "series" / series_id


def get_series_entity_registry_path(series_dir: Path, series_id: str) -> Path:
    """Get the series entity registry file path."""
    return series_dir / f"series_entities_{series_id}.json"


def save_series_entity_registry(
    series_id: str,
    entities: Mapping[str, SeriesEntityRecord],
    promotions: Tuple[EntityPromotionRecord, ...],
    registry_path: Path,
) -> Mapping[str, Any]:
    """
    Save SeriesEntityRegistry to disk with validation.

    Writes deterministic canonical JSON with series_entity_registry_fingerprint.
    Atomic write via temp file + os.replace.

    Returns metadata including file hash and record counts.
    """
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    # Build payload
    payload = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "series_id": series_id,
        "entities": [record.to_dict() for record in entities.values()],
        "promotions": [record.to_dict() for record in promotions],
    }

    # Compute fingerprint
    fingerprint = compute_series_entity_registry_fingerprint(payload)
    payload["series_entity_registry_fingerprint"] = fingerprint

    # Write canonical JSON
    canonical_json = to_canonical_json(payload)

    # Atomic write: temp file + os.replace
    temp_path = registry_path.with_suffix(".tmp")
    temp_path.write_text(canonical_json, encoding="utf-8", newline="\n")
    os.replace(temp_path, registry_path)

    # Compute file hash
    file_hash = compute_sha256(canonical_json)

    return {
        "file_hash": file_hash,
        "series_entity_registry_fingerprint": fingerprint,
        "schema_version": SCHEMA_VERSION,
        "entity_count": len(entities),
        "promotion_count": len(promotions),
    }


def load_series_entity_registry(
    registry_path: Path,
) -> Tuple[Mapping[str, SeriesEntityRecord], Tuple[EntityPromotionRecord, ...], str]:
    """
    Load SeriesEntityRegistry from disk with fail-closed validation.

    Returns:
        Tuple of (entities_dict, promotions_tuple, series_id)

    Raises:
        SeriesEntityValidationError: If file not found, invalid JSON, or schema mismatch
        SeriesEntityIntegrityError: If fingerprint doesn't match (fail-closed)
    """
    if not registry_path.exists():
        raise SeriesEntityValidationError(f"Series entity registry file not found: {registry_path}")

    content = registry_path.read_text(encoding="utf-8")
    if not content.strip():
        raise SeriesEntityValidationError(f"Series entity registry file is empty: {registry_path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SeriesEntityValidationError(
            f"Series entity registry file is not valid JSON: {registry_path}"
        ) from exc

    # Verify fingerprint (fail-closed)
    verify_series_entity_registry_fingerprint(
        data, data.get("series_entity_registry_fingerprint", "")
    )

    # Validate payload
    report = validate_series_entity_registry_payload(data)
    if not report.valid:
        raise SeriesEntityValidationError(
            f"Series entity registry validation failed: {'; '.join(report.errors)}"
        )

    series_id = data.get("series_id", "")
    entities = {
        SeriesEntityRecord.from_dict(record_data).series_entity_id: SeriesEntityRecord.from_dict(record_data)
        for record_data in data.get("entities", [])
    }
    promotions = tuple(
        EntityPromotionRecord.from_dict(promo_data)
        for promo_data in data.get("promotions", [])
    )

    return entities, promotions, series_id


def verify_series_entity_registry_integrity(
    registry_path: Path,
    expected_fingerprint: str,
) -> bool:
    """Verify series entity registry file matches expected fingerprint."""
    if not registry_path.exists():
        return False
    content = registry_path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return False
    computed = compute_series_entity_registry_fingerprint(data)
    return computed == expected_fingerprint


def create_empty_series_entity_registry(series_id: str) -> Mapping[str, SeriesEntityRecord]:
    """Create an empty SeriesEntityRegistry for a new series."""
    return {}


def ensure_series_dir(output_root: Path, series_id: str) -> Path:
    """Ensure series directory exists and return path."""
    series_dir = get_series_dir(output_root, series_id)
    series_dir.mkdir(parents=True, exist_ok=True)
    return series_dir


def compute_sha256(data: str | bytes) -> str:
    """Compute SHA-256 hex digest."""
    import hashlib
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
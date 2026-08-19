from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Tuple

from .models import (
    SeriesCharacterRecord,
    SeriesFactRecord,
    HydrationReport,
    PromotionRecord,
)
from .mapping import SeriesNamespaceMapping
from .validation import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    compute_series_memory_fingerprint,
    to_canonical_json,
    validate_series_memory_payload,
    verify_fingerprint,
    SeriesMemoryIntegrityError,
    SeriesMemoryValidationError,
)


def get_series_dir(output_root: Path, series_id: str) -> Path:
    """Get the series directory path."""
    return output_root / "series" / series_id


def series_memory_file_path(series_dir: Path, series_id: str) -> Path:
    """Get the series memory file path."""
    return series_dir / f"series_memory_{series_id}.json"


def save_series_memory(
    mapping: SeriesNamespaceMapping,
    series_id: str,
    memory_file: Path,
    promotion_records: Tuple[PromotionRecord, ...] = (),
) -> Mapping[str, Any]:
    """
    Save SeriesMemoryStore to disk with validation.

    Writes deterministic canonical JSON with series_memory_fingerprint.

    Returns metadata including file hash and record counts.
    """
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    # Use the mapping's internal format for round-trip compatibility
    mapping_dict = mapping.to_dict()
    mapping_dict["schema_name"] = SCHEMA_NAME
    mapping_dict["schema_version"] = SCHEMA_VERSION
    mapping_dict["series_id"] = series_id
    mapping_dict["promotions"] = [record.to_dict() for record in promotion_records]

    fingerprint = compute_series_memory_fingerprint(mapping_dict)
    mapping_dict["series_memory_fingerprint"] = fingerprint

    canonical_json = to_canonical_json(mapping_dict)
    memory_file.write_text(canonical_json, encoding="utf-8", newline="\n")

    file_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    return {
        "file_hash": file_hash,
        "series_memory_fingerprint": fingerprint,
        "schema_version": SCHEMA_VERSION,
        "character_count": len(mapping.get_all_characters()),
        "fact_count": len(mapping.get_all_facts()),
        "promotion_count": len(promotion_records),
    }


def load_series_memory(memory_file: Path) -> Tuple[SeriesNamespaceMapping, Tuple[PromotionRecord, ...]]:
    """
    Load SeriesMemoryStore from disk with fail-closed validation.

    Returns:
        Tuple of (SeriesNamespaceMapping, promotion_records)

    Raises:
        SeriesMemoryValidationError: If file not found, invalid JSON, or schema mismatch
        SeriesMemoryIntegrityError: If fingerprint doesn't match (fail-closed)
    """
    if not memory_file.exists():
        raise SeriesMemoryValidationError(f"Series memory file not found: {memory_file}")

    content = memory_file.read_text(encoding="utf-8")
    if not content.strip():
        raise SeriesMemoryValidationError(f"Series memory file is empty: {memory_file}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SeriesMemoryValidationError(
            f"Series memory file is not valid JSON: {memory_file}"
        ) from exc

    verify_fingerprint(data, data.get("series_memory_fingerprint", ""))

    report = validate_series_memory_payload(data)
    if not report.valid:
        raise SeriesMemoryValidationError(
            f"Series memory validation failed: {'; '.join(report.errors)}"
        )

    mapping = SeriesNamespaceMapping.from_dict(data)
    promotions = tuple(
        PromotionRecord(**item) for item in data.get("promotions", [])
    )

    return mapping, promotions


def verify_series_memory_integrity(memory_file: Path, expected_fingerprint: str) -> bool:
    """Verify series memory file matches expected fingerprint."""
    if not memory_file.exists():
        return False
    content = memory_file.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return False
    computed = compute_series_memory_fingerprint(data)
    return computed == expected_fingerprint


def create_empty_series_memory(series_id: str) -> SeriesNamespaceMapping:
    """Create an empty SeriesNamespaceMapping for a new series."""
    return SeriesNamespaceMapping()


def ensure_series_dir(output_root: Path, series_id: str) -> Path:
    """Ensure series directory exists and return path."""
    series_dir = get_series_dir(output_root, series_id)
    series_dir.mkdir(parents=True, exist_ok=True)
    return series_dir
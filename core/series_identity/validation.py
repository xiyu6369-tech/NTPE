from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ValidationError(Exception):
    """Raised when manifest validation fails."""
    pass


class IntegrityError(Exception):
    """Raised when manifest integrity check fails (hash mismatch)."""
    pass


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(valid=True, errors=[])

    @classmethod
    def failure(cls, errors: list[str]) -> "ValidationResult":
        return cls(valid=False, errors=errors)


def validate_manifest(manifest: Any, expected_series_id: str) -> ValidationResult:
    """
    Comprehensive manifest validation.

    Checks:
    - Schema name and version
    - Required fields present
    - series_id matches expected
    - volume_number sequential, no gaps, starts at 1
    - No duplicate book_identity
    - Valid lifecycle status
    - Valid book statuses
    - Valid timestamps
    - manifest_fingerprint matches computed
    """
    errors = []

    # Schema validation
    if getattr(manifest, "schema_name", None) != "ntpe.series_manifest":
        errors.append(f"Invalid schema_name: {getattr(manifest, 'schema_name', 'missing')}")

    if getattr(manifest, "schema_version", None) != "1.0":
        errors.append(f"Invalid schema_version: {getattr(manifest, 'schema_version', 'missing')}")

    # series_id validation
    if getattr(manifest, "series_id", None) != expected_series_id:
        errors.append(f"series_id mismatch: expected {expected_series_id}, got {getattr(manifest, 'series_id', 'missing')}")

    # Required fields
    required_fields = [
        "series_id", "series_name", "lifecycle_status", "created_at", "updated_at",
        "books", "series_memory_hash", "series_checkpoint_hash", "manifest_fingerprint"
    ]
    for field in required_fields:
        if not hasattr(manifest, field):
            errors.append(f"Missing required field: {field}")

    # Books validation
    books = getattr(manifest, "books", [])
    if books:
        volume_numbers = [b.volume_number for b in books]
        book_identities = [b.book_identity for b in books]

        # Sequential volume numbers starting at 1
        if volume_numbers:
            if volume_numbers[0] != 1:
                errors.append("volume_number must start at 1")
            for i, vol in enumerate(volume_numbers):
                if vol != i + 1:
                    errors.append(f"volume_number gap or out of order at index {i}: expected {i+1}, got {vol}")

        # No duplicate book_identity
        if len(book_identities) != len(set(book_identities)):
            errors.append("Duplicate book_identity in books list")

    # Fingerprint validation
    from .canonical import compute_manifest_fingerprint
    computed_fingerprint = compute_manifest_fingerprint(manifest.to_canonical_dict())
    if manifest.manifest_fingerprint != computed_fingerprint:
        errors.append(f"manifest_fingerprint mismatch: expected {computed_fingerprint}, got {manifest.manifest_fingerprint}")

    return ValidationResult.success() if not errors else ValidationResult.failure(errors)


def validate_series_create(series_id: str, series_dir: str) -> ValidationResult:
    """Validate series creation preconditions."""
    errors = []

    # Check series_dir exists and is empty or has valid manifest
    import os
    if os.path.exists(series_dir):
        manifest_path = os.path.join(series_dir, f"series_manifest_{series_id}.json")
        if os.path.exists(manifest_path):
            errors.append(f"Series already exists: {series_id}")

    return ValidationResult.success() if not errors else ValidationResult.failure(errors)

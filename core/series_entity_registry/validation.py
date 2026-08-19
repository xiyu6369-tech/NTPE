"""P0 Stage 5 Batch 5.3 — Series Entity Registry Validation.

Schema validation, fingerprint verification, fail-closed integrity checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from .models import (
    SeriesEntityRecord,
    EntityPromotionRecord,
    ConflictRecord,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    EntityType,
    RecordLifecycle,
    InjectionSource,
    PromotionAction,
)


@dataclass(frozen=True)
class ValidationReport:
    """Report of validation results."""
    valid: bool
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]

    @classmethod
    def success(cls) -> "ValidationReport":
        return cls(valid=True, errors=(), warnings=())

    @classmethod
    def failure(cls, errors: Tuple[str, ...], warnings: Tuple[str, ...] = ()) -> "ValidationReport":
        return cls(valid=False, errors=errors, warnings=warnings)


class SeriesEntityValidationError(Exception):
    """Raised when series entity validation fails."""
    pass


class SeriesEntityIntegrityError(Exception):
    """Raised when series entity integrity check fails (fail-closed)."""
    pass


def to_canonical_json(obj: Mapping[str, Any]) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_sha256(data: str | bytes) -> str:
    """Compute SHA-256 hex digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_series_entity_registry_fingerprint(payload: Mapping[str, Any]) -> str:
    """Compute SHA-256 of canonical registry payload (excluding fingerprint itself)."""
    filtered = {k: v for k, v in payload.items() if k != "series_entity_registry_fingerprint"}
    canonical = to_canonical_json(filtered)
    return compute_sha256(canonical)


def validate_series_entity_record(record: SeriesEntityRecord) -> ValidationReport:
    """Validate a SeriesEntityRecord (SE-2: minimal model, SE-5: per-record version)."""
    errors = []
    warnings = []

    # series_entity_id format
    if not record.series_entity_id:
        errors.append("series_entity_id cannot be empty")
    elif not record.series_entity_id.startswith("sentity_"):
        errors.append(f"series_entity_id must start with 'sentity_': {record.series_entity_id}")

    # series_id
    if not record.series_id:
        errors.append("series_id cannot be empty")

    # source_name
    if not record.source_name:
        errors.append("source_name cannot be empty")

    # entity_type (SE-1: RM-7.2 set only)
    try:
        EntityType(record.entity_type.value)
    except ValueError:
        errors.append(f"Invalid entity_type: {record.entity_type.value}. Must be one of: {[e.value for e in EntityType]}")

    # canonical_target
    if not record.canonical_target:
        errors.append("canonical_target cannot be empty")

    # version (SE-5: per-record versioning, starts at 1)
    if record.version < 1:
        errors.append(f"version must be >= 1, got {record.version}")

    # lifecycle
    try:
        RecordLifecycle(record.lifecycle.value)
    except ValueError:
        errors.append(f"Invalid lifecycle: {record.lifecycle.value}")

    # metadata
    if not isinstance(record.metadata, dict):
        errors.append("metadata must be a dict")
    else:
        # Recommended fields
        if "source_books" not in record.metadata:
            warnings.append("metadata missing 'source_books'")
        if "book_coverage" not in record.metadata:
            warnings.append("metadata missing 'book_coverage'")

    # approved_at
    if not record.approved_at:
        errors.append("approved_at cannot be empty")

    # approved_by
    if not record.approved_by:
        errors.append("approved_by cannot be empty")
    elif record.approved_by not in ("user", "series_promotion"):
        warnings.append(f"approved_by should be 'user' or 'series_promotion', got '{record.approved_by}'")

    # created_at
    if not record.created_at:
        errors.append("created_at cannot be empty")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def validate_entity_promotion_record(record: EntityPromotionRecord) -> ValidationReport:
    """Validate an EntityPromotionRecord."""
    errors = []
    warnings = []

    if not record.promotion_id:
        errors.append("promotion_id cannot be empty")

    if not record.series_id:
        errors.append("series_id cannot be empty")

    if not record.book_identity:
        errors.append("book_identity cannot be empty")

    if not record.source_name:
        errors.append("source_name cannot be empty")

    try:
        EntityType(record.entity_type.value)
    except ValueError:
        errors.append(f"Invalid entity_type: {record.entity_type.value}")

    if not record.new_target:
        errors.append("new_target cannot be empty")

    try:
        PromotionAction(record.action.value)
    except ValueError:
        errors.append(f"Invalid action: {record.action.value}")

    if not record.resolved_at:
        errors.append("resolved_at cannot be empty")

    if record.source_level not in ("USER_OVERRIDE", "LEARNING"):
        warnings.append(f"source_level should be 'USER_OVERRIDE' or 'LEARNING', got '{record.source_level}'")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def validate_series_entity_registry_payload(payload: Mapping[str, Any]) -> ValidationReport:
    """Validate the full series entity registry payload on load."""
    errors = []
    warnings = []

    if payload.get("schema_name") != SCHEMA_NAME:
        errors.append(f"Invalid schema_name: expected '{SCHEMA_NAME}', got '{payload.get('schema_name')}'")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Invalid schema_version: expected '{SCHEMA_VERSION}', got '{payload.get('schema_version')}'")

    if "series_entity_registry_fingerprint" not in payload:
        errors.append("Missing series_entity_registry_fingerprint")

    series_id = payload.get("series_id")
    if not series_id:
        errors.append("Missing series_id")

    entities = payload.get("entities", [])
    if not isinstance(entities, list):
        errors.append("entities must be a list")
    else:
        seen_ids = set()
        for i, entity_data in enumerate(entities):
            try:
                record = SeriesEntityRecord.from_dict(entity_data)
                report = validate_series_entity_record(record)
                if not report.valid:
                    errors.extend(f"Entity[{i}]: {e}" for e in report.errors)
                warnings.extend(f"Entity[{i}]: {w}" for w in report.warnings)

                # Check for duplicate series_entity_id
                if record.series_entity_id in seen_ids:
                    errors.append(f"Entity[{i}]: duplicate series_entity_id: {record.series_entity_id}")
                seen_ids.add(record.series_entity_id)

                # Verify series_entity_id matches computed (namespace isolation)
                expected_id = compute_series_entity_id(
                    record.series_id, record.source_name, record.entity_type.value
                )
                if record.series_entity_id != expected_id:
                    errors.append(
                        f"Entity[{i}]: series_entity_id mismatch. "
                        f"Expected {expected_id}, got {record.series_entity_id}"
                    )

            except Exception as e:
                errors.append(f"Entity[{i}]: Failed to parse - {e}")

    promotions = payload.get("promotions", [])
    if not isinstance(promotions, list):
        errors.append("promotions must be a list")
    else:
        for i, promo_data in enumerate(promotions):
            try:
                record = EntityPromotionRecord.from_dict(promo_data)
                report = validate_entity_promotion_record(record)
                if not report.valid:
                    errors.extend(f"Promotion[{i}]: {e}" for e in report.errors)
                warnings.extend(f"Promotion[{i}]: {w}" for w in report.warnings)
            except Exception as e:
                errors.append(f"Promotion[{i}]: Failed to parse - {e}")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def compute_series_entity_id(series_id: str, source_name: str, entity_type: str) -> str:
    """Compute namespace-isolated entity ID (SE-3: typed)."""
    return f"sentity_{compute_sha256(f'{series_id}|{source_name.strip()}|{entity_type.upper()}')[:16]}"


def verify_series_entity_registry_fingerprint(
    payload: Mapping[str, Any],
    expected_fingerprint: str
) -> None:
    """Verify SHA-256 fingerprint matches computed fingerprint (fail-closed)."""
    computed = compute_series_entity_registry_fingerprint(payload)
    if computed != expected_fingerprint:
        raise SeriesEntityIntegrityError(
            f"Fingerprint mismatch: expected {expected_fingerprint}, computed {computed}. "
            f"File may be corrupted or tampered."
        )
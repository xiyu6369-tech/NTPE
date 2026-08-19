from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from .models import (
    SeriesCharacterRecord,
    SeriesFactRecord,
    ApprovalStatus,
    FactType,
    Evidence,
    EvidenceType,
)


SCHEMA_NAME = "ntpe.series_memory"
SCHEMA_VERSION = "1.0"


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


class SeriesMemoryValidationError(Exception):
    """Raised when series memory validation fails."""
    pass


class SeriesMemoryIntegrityError(Exception):
    """Raised when series memory integrity check fails (fail-closed)."""
    pass


ALLOWED_HYDRATION_FACT_TYPES = frozenset({
    FactType.CANONICAL_NAME,
    FactType.NAME_VARIANT,
    FactType.RELATIONSHIP,
    FactType.ROLE_OR_IDENTITY,
    FactType.TERMINOLOGY_PREFERENCE,
    FactType.PRONOUN_OR_GENDER_REFERENCE,
    FactType.APPEARANCE,
})


FORBIDDEN_HYDRATION_FACT_TYPES = frozenset({
    FactType.TEMPORAL_STATE,
    FactType.LOCATION_STATE,
    FactType.SPEECH_STYLE,
    FactType.ADDRESSING_STYLE,
    FactType.PERSONALITY_TRAIT,
    FactType.OTHER,
})


def validate_evidence(evidence: Evidence) -> None:
    """Validate a single evidence item."""
    if not evidence.evidence_id:
        raise SeriesMemoryValidationError("evidence_id cannot be empty")
    if not evidence.source_case_id:
        raise SeriesMemoryValidationError("source_case_id cannot be empty")
    if not evidence.source_segment_id:
        raise SeriesMemoryValidationError("source_segment_id cannot be empty")
    if not evidence.source_text_hash:
        raise SeriesMemoryValidationError("source_text_hash cannot be empty")
    if not evidence.excerpt:
        raise SeriesMemoryValidationError("excerpt cannot be empty")
    if not evidence.language:
        raise SeriesMemoryValidationError("language cannot be empty")
    if not evidence.observed_at:
        raise SeriesMemoryValidationError("observed_at cannot be empty")
    try:
        EvidenceType(evidence.evidence_type.value)
    except ValueError:
        raise SeriesMemoryValidationError(f"Invalid evidence_type: {evidence.evidence_type}")


def validate_series_character_record(record: SeriesCharacterRecord) -> ValidationReport:
    """Validate a SeriesCharacterRecord."""
    errors = []
    warnings = []

    if not record.series_character_id:
        errors.append("series_character_id cannot be empty")
    elif not record.series_character_id.startswith("schar_"):
        errors.append(f"series_character_id must start with 'schar_': {record.series_character_id}")

    if not record.korean_name:
        errors.append("korean_name cannot be empty")

    if not record.canonical_name:
        errors.append("canonical_name cannot be empty")

    if not record.value:
        errors.append("value cannot be empty")

    if record.fact_type not in ALLOWED_HYDRATION_FACT_TYPES:
        errors.append(f"fact_type {record.fact_type.value} not allowed for SeriesMemoryStore")

    if record.approval_status != ApprovalStatus.APPROVED:
        errors.append(f"SeriesCharacterRecord must have APPROVED status, got {record.approval_status.value}")

    if not 0.0 <= record.confidence <= 1.0:
        errors.append(f"confidence must be in [0.0, 1.0], got {record.confidence}")

    if record.version < 1:
        errors.append(f"version must be >= 1, got {record.version}")

    if not record.created_at:
        errors.append("created_at cannot be empty")

    if not record.updated_at:
        errors.append("updated_at cannot be empty")

    if not record.source_books:
        warnings.append("source_books is empty")

    for ev in record.evidence:
        try:
            validate_evidence(ev)
        except SeriesMemoryValidationError as e:
            errors.append(f"Invalid evidence: {e}")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def validate_series_fact_record(record: SeriesFactRecord) -> ValidationReport:
    """Validate a SeriesFactRecord."""
    errors = []
    warnings = []

    if not record.series_fact_id:
        errors.append("series_fact_id cannot be empty")
    elif not record.series_fact_id.startswith("sfact_"):
        errors.append(f"series_fact_id must start with 'sfact_': {record.series_fact_id}")

    if not record.value:
        errors.append("value cannot be empty")

    if record.approval_status != ApprovalStatus.APPROVED:
        errors.append(f"SeriesFactRecord must have APPROVED status, got {record.approval_status.value}")

    if not 0.0 <= record.confidence <= 1.0:
        errors.append(f"confidence must be in [0.0, 1.0], got {record.confidence}")

    if record.version < 1:
        errors.append(f"version must be >= 1, got {record.version}")

    if not record.created_at:
        errors.append("created_at cannot be empty")

    if not record.updated_at:
        errors.append("updated_at cannot be empty")

    if not record.source_books:
        warnings.append("source_books is empty")

    for ev in record.evidence:
        try:
            validate_evidence(ev)
        except SeriesMemoryValidationError as e:
            errors.append(f"Invalid evidence: {e}")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def validate_series_memory_payload(payload: Mapping[str, Any]) -> ValidationReport:
    """Validate the full series memory payload on load."""
    errors = []
    warnings = []

    if payload.get("schema_name") != SCHEMA_NAME:
        errors.append(f"Invalid schema_name: expected '{SCHEMA_NAME}', got '{payload.get('schema_name')}'")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Invalid schema_version: expected '{SCHEMA_VERSION}', got '{payload.get('schema_version')}'")

    if "series_memory_fingerprint" not in payload:
        errors.append("Missing series_memory_fingerprint")

    characters = payload.get("characters", [])
    facts = payload.get("facts", [])

    if not isinstance(characters, list):
        errors.append("characters must be a list")
    else:
        for i, char_data in enumerate(characters):
            try:
                record = SeriesCharacterRecord.from_dict(char_data)
                report = validate_series_character_record(record)
                if not report.valid:
                    errors.extend(f"Character[{i}]: {e}" for e in report.errors)
                warnings.extend(f"Character[{i}]: {w}" for w in report.warnings)
            except Exception as e:
                errors.append(f"Character[{i}]: Failed to parse - {e}")

    if not isinstance(facts, list):
        errors.append("facts must be a list")
    else:
        for i, fact_data in enumerate(facts):
            try:
                record = SeriesFactRecord.from_dict(fact_data)
                report = validate_series_fact_record(record)
                if not report.valid:
                    errors.extend(f"Fact[{i}]: {e}" for e in report.errors)
                warnings.extend(f"Fact[{i}]: {w}" for w in report.warnings)
            except Exception as e:
                errors.append(f"Fact[{i}]: Failed to parse - {e}")

    if errors:
        return ValidationReport.failure(tuple(errors), tuple(warnings))
    return ValidationReport.success()


def validate_hydration_scope(fact_type: FactType) -> bool:
    """Check if a fact type is allowed for Series → Book hydration."""
    return fact_type in ALLOWED_HYDRATION_FACT_TYPES


def check_hydration_forbidden(fact_type: FactType) -> Optional[str]:
    """Return error message if fact_type is forbidden for hydration, None if allowed."""
    if fact_type in FORBIDDEN_HYDRATION_FACT_TYPES:
        return f"FactType {fact_type.value} is forbidden for Series→Book hydration (transient/book-local scope)"
    if fact_type not in ALLOWED_HYDRATION_FACT_TYPES:
        return f"FactType {fact_type.value} is not in allowed hydration list"
    return None


def verify_fingerprint(payload: Mapping[str, Any], expected_fingerprint: str) -> None:
    """Verify SHA-256 fingerprint matches computed fingerprint (fail-closed)."""
    computed = compute_series_memory_fingerprint(payload)
    if computed != expected_fingerprint:
        raise SeriesMemoryIntegrityError(
            f"Fingerprint mismatch: expected {expected_fingerprint}, computed {computed}. "
            f"File may be corrupted or tampered."
        )


def compute_series_memory_fingerprint(payload: Mapping[str, Any]) -> str:
    """Compute SHA-256 of canonical series memory payload."""
    import hashlib
    canonical_json = to_canonical_json({
        k: v for k, v in payload.items() if k != "series_memory_fingerprint"
    })
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def to_canonical_json(obj: Mapping[str, Any]) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
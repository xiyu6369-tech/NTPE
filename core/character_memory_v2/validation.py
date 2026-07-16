from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping

from .models import (
    ApprovalStatus,
    Evidence,
    EvidenceType,
    ExpiryKind,
    FactType,
    MAX_EVIDENCE_EXCERPT_CHARS,
    MemoryRecord,
    MemoryStatus,
    SCHEMA_VERSION,
)
from .normalization import normalize_text, normalized_identity


class CharacterMemoryValidationError(ValueError):
    pass


_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.I)
_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
_SECRET_PATTERNS = (
    re.compile(r"nvapi-[A-Za-z0-9._-]+", re.I),
    re.compile(r"(?:sk|key)-[A-Za-z0-9_-]{20,}", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
    re.compile(r"Authorization\s*:\s*[^\s]+", re.I),
    re.compile(r"api[_-]?key\s*=\s*['\"][^'\"]{8,}", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def parse_timestamp(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CharacterMemoryValidationError(f"{field_name} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CharacterMemoryValidationError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise CharacterMemoryValidationError(f"{field_name} must include timezone")
    return parsed


def ensure_no_secret(value: str, field_name: str) -> None:
    if any(pattern.search(value) for pattern in _SECRET_PATTERNS):
        raise CharacterMemoryValidationError(f"{field_name} contains secret-like material")


def validate_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise CharacterMemoryValidationError(f"{field_name} must be an explicit stable identifier")
    if any(part in {"..", "."} for part in value.replace("\\", "/").split("/")) or "/" in value or "\\" in value:
        raise CharacterMemoryValidationError(f"{field_name} cannot contain path traversal or separators")


def validate_evidence(evidence: Evidence) -> None:
    validate_identifier(evidence.evidence_id, "evidence_id")
    validate_identifier(evidence.source_case_id, "source_case_id")
    validate_identifier(evidence.source_segment_id, "source_segment_id")
    if not _SHA256.fullmatch(evidence.source_text_hash):
        raise CharacterMemoryValidationError("source_text_hash must be a SHA-256 hex digest")
    if not evidence.excerpt or len(evidence.excerpt) > MAX_EVIDENCE_EXCERPT_CHARS:
        raise CharacterMemoryValidationError(f"evidence excerpt must be 1..{MAX_EVIDENCE_EXCERPT_CHARS} characters")
    if not normalize_text(evidence.language):
        raise CharacterMemoryValidationError("evidence language is required")
    parse_timestamp(evidence.observed_at, "observed_at")
    ensure_no_secret(evidence.excerpt, "evidence excerpt")


def validate_record(record: MemoryRecord) -> None:
    validate_identifier(record.memory_id, "memory_id")
    validate_identifier(record.character_id, "character_id")
    if not normalize_text(record.value):
        raise CharacterMemoryValidationError("memory value is required")
    ensure_no_secret(record.value, "memory value")
    if not 0.0 <= record.confidence <= 1.0:
        raise CharacterMemoryValidationError("confidence must be between 0.0 and 1.0")
    if not isinstance(record.version, int) or isinstance(record.version, bool) or record.version < 1:
        raise CharacterMemoryValidationError("version must be a positive integer")
    parse_timestamp(record.created_at, "created_at")
    parse_timestamp(record.updated_at, "updated_at")
    if parse_timestamp(record.updated_at, "updated_at") < parse_timestamp(record.created_at, "created_at"):
        raise CharacterMemoryValidationError("updated_at cannot precede created_at")
    if not record.evidence:
        raise CharacterMemoryValidationError("memory requires structured evidence")
    evidence_ids = set()
    for item in record.evidence:
        validate_evidence(item)
        if item.evidence_id in evidence_ids:
            raise CharacterMemoryValidationError("duplicate evidence_id in record")
        evidence_ids.add(item.evidence_id)
    if record.evidence_type not in {item.evidence_type for item in record.evidence}:
        raise CharacterMemoryValidationError("primary evidence_type must appear in evidence")
    if not any(record.source_case_id == item.source_case_id and record.source_segment_id == item.source_segment_id for item in record.evidence):
        raise CharacterMemoryValidationError("record source identity must match attached evidence")
    if record.fact_type in {FactType.CANONICAL_NAME, FactType.NAME_VARIANT} and not record.evidence:
        raise CharacterMemoryValidationError("name facts require evidence")
    if record.fact_type in {FactType.TEMPORAL_STATE, FactType.LOCATION_STATE} and record.expiry_policy.kind == ExpiryKind.NEVER:
        raise CharacterMemoryValidationError("temporal and location facts cannot default to never expiry")
    validate_expiry(record)
    if record.approval_status == ApprovalStatus.APPROVED:
        if record.approval_metadata is None:
            raise CharacterMemoryValidationError("approved memory requires approval metadata")
        if normalized_identity(record.approval_metadata.approved_value) != normalized_identity(record.value):
            raise CharacterMemoryValidationError("approved value must match memory value")
        parse_timestamp(record.approval_metadata.approved_at, "approved_at")
    elif record.approval_metadata is not None:
        raise CharacterMemoryValidationError("approval metadata requires approved status")
    if record.evidence_type == EvidenceType.AI_INFERENCE and record.approval_status == ApprovalStatus.APPROVED:
        raise CharacterMemoryValidationError("AI inference cannot become approved without separate human-approved evidence")
    if record.evidence_type == EvidenceType.HUMAN_REJECTED and record.status != MemoryStatus.REJECTED:
        raise CharacterMemoryValidationError("human-rejected evidence requires rejected status")
    if record.unresolved_identity and record.fact_type == FactType.CANONICAL_NAME and record.approval_status != ApprovalStatus.APPROVED:
        raise CharacterMemoryValidationError("unresolved identity cannot establish an unapproved canonical name")


def validate_expiry(record: MemoryRecord) -> None:
    policy = record.expiry_policy
    if policy.kind in {ExpiryKind.SEGMENT_SCOPE, ExpiryKind.CHAPTER_SCOPE, ExpiryKind.SESSION_SCOPE}:
        if not policy.scope_id:
            raise CharacterMemoryValidationError(f"{policy.kind.value} requires scope_id")
        validate_identifier(policy.scope_id, "expiry scope_id")
        if policy.expires_at is not None:
            raise CharacterMemoryValidationError("scope expiry cannot also specify expires_at")
    elif policy.kind == ExpiryKind.TIMESTAMP:
        if not policy.expires_at:
            raise CharacterMemoryValidationError("timestamp expiry requires expires_at")
        parse_timestamp(policy.expires_at, "expires_at")
        if policy.scope_id is not None:
            raise CharacterMemoryValidationError("timestamp expiry cannot specify scope_id")
    elif policy.scope_id is not None or policy.expires_at is not None:
        raise CharacterMemoryValidationError(f"{policy.kind.value} does not accept scope/timestamp data")


def validate_store_payload(payload: Mapping[str, Any]) -> None:
    required = {"schema_version", "records", "history", "conflicts", "snapshot_version"}
    if set(payload) != required:
        missing = sorted(required - set(payload))
        extra = sorted(set(payload) - required)
        raise CharacterMemoryValidationError(f"invalid store fields; missing={missing}, extra={extra}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise CharacterMemoryValidationError("unknown character memory schema version")
    if not isinstance(payload.get("records"), list) or not isinstance(payload.get("history"), dict) or not isinstance(payload.get("conflicts"), list):
        raise CharacterMemoryValidationError("records/history/conflicts have invalid shape")
    version = payload.get("snapshot_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise CharacterMemoryValidationError("snapshot_version must be a non-negative integer")


def validate_memory_store(store: Any) -> dict[str, Any]:
    errors: list[str] = []
    if getattr(store, "schema_version", None) != SCHEMA_VERSION:
        errors.append("unknown schema_version")
    records = getattr(store, "records", {})
    for memory_id, record in records.items():
        try:
            if memory_id != record.memory_id:
                raise CharacterMemoryValidationError("record key does not match memory_id")
            validate_record(record)
        except (CharacterMemoryValidationError, ValueError, TypeError) as exc:
            errors.append(f"{memory_id}: {exc}")
    return {"valid": not errors, "errors": errors, "record_count": len(records), "schema_version": getattr(store, "schema_version", None)}

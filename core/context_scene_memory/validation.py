from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .models import (
    ApprovalStatus, ContextEvidence, ContextMemoryRecord, ContextType, EvidenceType,
    ExpiryKind, MAX_CONTEXT_EXCERPT_CHARS, MAX_CONTEXT_VALUE_CHARS, RecordStatus,
    ResolutionStatus, SceneMemoryRecord, SCHEMA_VERSION,
)
from .normalization import normalize_text


class ContextSceneValidationError(ValueError):
    pass


_SHA = re.compile(r"^[0-9a-f]{64}$", re.I)
_ID = re.compile(r"^[A-Za-z0-9._:-]{1,180}$")
_SECRETS = (
    re.compile(r"nvapi-[A-Za-z0-9._-]{16,}", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
    re.compile(r"Authorization\s*:\s*[A-Za-z0-9._-]{12,}", re.I),
    re.compile(r"api[_-]?key\s*=\s*[^\s,]{8,}", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def parse_timestamp(value: str, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ContextSceneValidationError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContextSceneValidationError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ContextSceneValidationError(f"{name} must include timezone")
    return parsed


def validate_identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value) or "/" in value or "\\" in value or value in {".", ".."}:
        raise ContextSceneValidationError(f"{name} must be a stable non-path identifier")


def _safe_text(value: str, name: str, maximum: int) -> None:
    if not normalize_text(value) or len(value) > maximum:
        raise ContextSceneValidationError(f"{name} must be 1..{maximum} characters")
    if any(pattern.search(value) for pattern in _SECRETS):
        raise ContextSceneValidationError(f"{name} contains secret-like material")


def validate_evidence(item: ContextEvidence) -> None:
    validate_identifier(item.evidence_id, "evidence_id")
    validate_identifier(item.source_case_id, "source_case_id")
    validate_identifier(item.source_segment_id, "source_segment_id")
    if item.source_text_hash is not None and not _SHA.fullmatch(item.source_text_hash):
        raise ContextSceneValidationError("source_text_hash must be SHA-256")
    if item.translation_text_hash is not None and not _SHA.fullmatch(item.translation_text_hash):
        raise ContextSceneValidationError("translation_text_hash must be SHA-256")
    if item.evidence_type == EvidenceType.SOURCE_OBSERVATION and item.source_text_hash is None:
        raise ContextSceneValidationError("source observation requires source hash")
    if item.evidence_type == EvidenceType.TRANSLATION_OBSERVATION and item.translation_text_hash is None:
        raise ContextSceneValidationError("translation observation requires translation hash")
    if item.evidence_type == EvidenceType.RULE_DERIVED and not item.rule_id:
        raise ContextSceneValidationError("rule-derived evidence requires rule_id")
    if item.source_text_hash is None and item.translation_text_hash is None:
        raise ContextSceneValidationError("evidence requires a source or translation hash")
    _safe_text(item.excerpt, "evidence excerpt", MAX_CONTEXT_EXCERPT_CHARS)
    parse_timestamp(item.observed_at, "observed_at")


def validate_expiry(policy: Any) -> None:
    if policy.kind in {ExpiryKind.SEGMENT_SCOPE, ExpiryKind.SCENE_SCOPE, ExpiryKind.CHAPTER_SCOPE, ExpiryKind.SESSION_SCOPE}:
        if not policy.scope_id:
            raise ContextSceneValidationError("scoped expiry requires scope_id")
        validate_identifier(policy.scope_id, "expiry scope_id")
    elif policy.kind == ExpiryKind.TIMESTAMP:
        if not policy.expires_at:
            raise ContextSceneValidationError("timestamp expiry requires expires_at")
        parse_timestamp(policy.expires_at, "expires_at")
    elif policy.scope_id is not None or policy.expires_at is not None:
        raise ContextSceneValidationError("expiry policy contains unsupported scope data")


def validate_context_record(record: ContextMemoryRecord) -> None:
    validate_identifier(record.context_id, "context_id")
    _safe_text(record.value, "context value", MAX_CONTEXT_VALUE_CHARS)
    if not 0 <= record.confidence <= 1:
        raise ContextSceneValidationError("confidence must be between 0 and 1")
    if not isinstance(record.sequence_index, int) or isinstance(record.sequence_index, bool) or record.sequence_index < 0:
        raise ContextSceneValidationError("sequence_index must be non-negative")
    if record.version < 1:
        raise ContextSceneValidationError("version must be positive")
    if not record.evidence:
        raise ContextSceneValidationError("context requires evidence")
    for item in record.evidence:
        validate_evidence(item)
    if record.context_type == ContextType.PREVIOUS_TRANSLATION_EXCERPT:
        if len(record.value) > MAX_CONTEXT_EXCERPT_CHARS:
            raise ContextSceneValidationError("previous translation excerpt exceeds limit")
        if not any(item.evidence_type == EvidenceType.TRANSLATION_OBSERVATION for item in record.evidence):
            raise ContextSceneValidationError("previous translation requires translation observation")
        if record.expiry_policy.kind == ExpiryKind.NEVER:
            raise ContextSceneValidationError("previous translation cannot be permanent")
    if record.context_type in {ContextType.TEMPORAL_STATE, ContextType.LOCATION_STATE, ContextType.SPEAKER_STATE, ContextType.EVENT_STATE, ContextType.UNRESOLVED_REFERENCE} and record.expiry_policy.kind == ExpiryKind.NEVER:
        raise ContextSceneValidationError("temporary context cannot be permanent")
    if record.approval_status == ApprovalStatus.APPROVED and not any(item.evidence_type == EvidenceType.HUMAN_APPROVED for item in record.evidence):
        raise ContextSceneValidationError("approved context requires human-approved evidence")
    if any(item.evidence_type == EvidenceType.AI_INFERENCE for item in record.evidence) and record.approval_status == ApprovalStatus.APPROVED and not any(item.evidence_type == EvidenceType.HUMAN_APPROVED for item in record.evidence):
        raise ContextSceneValidationError("AI inference cannot masquerade as approved fact")
    validate_expiry(record.expiry_policy)
    parse_timestamp(record.created_at, "created_at")
    if parse_timestamp(record.updated_at, "updated_at") < parse_timestamp(record.created_at, "created_at"):
        raise ContextSceneValidationError("updated_at precedes created_at")


def validate_scene_record(scene: SceneMemoryRecord) -> None:
    validate_identifier(scene.scene_id, "scene_id")
    validate_identifier(scene.chapter_id, "chapter_id")
    if scene.scene_version < 1:
        raise ContextSceneValidationError("scene_version must be positive")
    parse_timestamp(scene.created_at, "created_at")
    parse_timestamp(scene.updated_at, "updated_at")
    for item in scene.evidence:
        validate_evidence(item)
    ids = set()
    for participant in scene.participants:
        validate_identifier(participant.character_id, "participant character_id")
        if participant.character_id in ids:
            raise ContextSceneValidationError("duplicate scene participant")
        ids.add(participant.character_id)
        if not 0 <= participant.presence_confidence <= 1:
            raise ContextSceneValidationError("presence confidence out of range")
    for reference in scene.unresolved_references:
        validate_identifier(reference.reference_id, "reference_id")
        if not 0 <= reference.confidence <= 1:
            raise ContextSceneValidationError("reference confidence out of range")
        if reference.resolution_status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.CANDIDATE} and reference.resolved_target is not None:
            raise ContextSceneValidationError("unresolved reference cannot have resolved target")
        if reference.resolution_status in {ResolutionStatus.RESOLVED, ResolutionStatus.HUMAN_APPROVED} and not reference.resolved_target:
            raise ContextSceneValidationError("resolved reference requires target")
        for item in reference.evidence:
            validate_evidence(item)
        validate_expiry(reference.expiry)


def validate_context_store(store: Any) -> dict[str, Any]:
    errors = []
    if getattr(store, "schema_version", None) != SCHEMA_VERSION:
        errors.append("unknown schema_version")
    for key, record in getattr(store, "contexts", {}).items():
        try:
            if key != record.context_id:
                raise ContextSceneValidationError("context key mismatch")
            validate_context_record(record)
        except (ValueError, TypeError) as exc:
            errors.append(f"{key}: {exc}")
    for key, scene in getattr(store, "scenes", {}).items():
        try:
            if key != scene.scene_id:
                raise ContextSceneValidationError("scene key mismatch")
            validate_scene_record(scene)
        except (ValueError, TypeError) as exc:
            errors.append(f"{key}: {exc}")
    return {"valid": not errors, "errors": errors, "context_count": len(getattr(store, "contexts", {})), "scene_count": len(getattr(store, "scenes", {})), "schema_version": getattr(store, "schema_version", None)}

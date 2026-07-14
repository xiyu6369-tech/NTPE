from __future__ import annotations

from datetime import datetime

from .governance_model import CorpusGovernanceRecord
from .integrity import SHA256_PATTERN, sha256_text
from .lifecycle import CorpusLifecycle
from .provenance import APPROVAL_SOURCE, GOVERNANCE_SCHEMA_VERSION, validate_human_actor


def _timestamp(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")


def _reason(value: str, field: str) -> None:
    if len(value.strip()) < 12:
        raise ValueError(f"{field} must be substantive")


def validate_governance_record(record: CorpusGovernanceRecord) -> CorpusGovernanceRecord:
    if not record.case_id.strip() or not record.revision_id.strip() or record.revision_number < 1:
        raise ValueError("governance case revision identity invalid")
    if record.revision_number == 1 and record.previous_revision_id is not None:
        raise ValueError("initial revision cannot have a previous revision")
    if record.revision_number > 1 and not record.previous_revision_id:
        raise ValueError("later revision requires previous revision identity")
    if record.governance_schema_version != GOVERNANCE_SCHEMA_VERSION:
        raise ValueError("unsupported governance schema version")
    evidence = record.source_evidence
    if evidence.schema_version != GOVERNANCE_SCHEMA_VERSION:
        raise ValueError("unsupported source evidence schema version")
    if not evidence.source_language.strip() or not evidence.target_language.strip() or not evidence.source_artifact_reference.strip():
        raise ValueError("source evidence metadata is required")
    for digest in (evidence.source_text_sha256, evidence.source_artifact_sha256):
        if SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError("source evidence requires lowercase SHA-256 values")
    _timestamp(evidence.created_at, "source evidence created_at")
    if not record.audit_history:
        raise ValueError("governance audit history is required")
    for event in record.audit_history:
        validate_human_actor(event.actor)
        _reason(event.reason, "audit reason")
        _timestamp(event.occurred_at, "audit occurred_at")
    active_approval = record.status in {CorpusLifecycle.APPROVED, CorpusLifecycle.SUPERSEDED, CorpusLifecycle.DEPRECATED}
    if active_approval:
        if not record.approved_final_translation or record.approval is None:
            raise ValueError("approved lifecycle requires approved translation provenance")
        approval = record.approval
        validate_human_actor(approval.human_approver)
        _reason(approval.approval_reason, "approval reason")
        _timestamp(approval.approved_at, "approved_at")
        if approval.approval_source != APPROVAL_SOURCE:
            raise ValueError("approval source must be human_governance_review")
        if approval.governance_schema_version != GOVERNANCE_SCHEMA_VERSION:
            raise ValueError("approval governance schema version invalid")
        if approval.source_text_sha256 != evidence.source_text_sha256:
            raise ValueError("approval source evidence mismatch")
        if approval.approved_translation_sha256 != sha256_text(record.approved_final_translation):
            raise ValueError("approved translation integrity mismatch")
        for digest in (approval.review_artifact_sha256, approval.metrics_sha256, approval.defects_sha256):
            if SHA256_PATTERN.fullmatch(digest) is None:
                raise ValueError("approval evidence requires lowercase SHA-256 values")
    elif record.approved_final_translation is not None or record.approval is not None:
        raise ValueError("unapproved lifecycle must retain a null approved translation")
    if record.status is CorpusLifecycle.SUPERSEDED and record.supersession is None:
        raise ValueError("superseded case requires supersession metadata")
    if record.status is CorpusLifecycle.DEPRECATED and record.deprecation is None:
        raise ValueError("deprecated case requires deprecation metadata")
    if record.status is CorpusLifecycle.REJECTED:
        if record.rejection is None:
            raise ValueError("rejected case requires rejection metadata")
        if record.approved_final_translation is not None:
            raise ValueError("rejected case cannot have an approved translation")
    return record


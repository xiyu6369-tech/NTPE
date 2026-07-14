from __future__ import annotations

from dataclasses import replace

from core.translation_quality_review_decision import HumanReviewDecision, ReviewDecisionStatus

from .governance_model import ApprovalProvenance, AuditEvent, CorpusGovernanceRecord, DeprecationMetadata, RejectionMetadata, SupersessionMetadata
from .governance_validator import validate_governance_record
from .integrity import sha256_text, verify_corpus_integrity
from .lifecycle import CorpusLifecycle, validate_lifecycle_transition
from .provenance import APPROVAL_SOURCE, GOVERNANCE_SCHEMA_VERSION, validate_human_actor


def _event(record: CorpusGovernanceRecord, action: str, actor: str, reason: str, at: str, target: CorpusLifecycle) -> tuple[AuditEvent, ...]:
    return record.audit_history + (AuditEvent(action, actor, reason, at, record.status.value, target.value),)


def _transition(record: CorpusGovernanceRecord, target: CorpusLifecycle, actor: str, reason: str, at: str, action: str) -> CorpusGovernanceRecord:
    validate_human_actor(actor)
    validate_lifecycle_transition(record.status, target)
    return validate_governance_record(replace(record, status=target, audit_history=_event(record, action, actor, reason, at, target)))


def submit_corpus_case_for_review(record: CorpusGovernanceRecord, *, reviewer: str, reason: str, submitted_at: str) -> CorpusGovernanceRecord:
    return _transition(record, CorpusLifecycle.UNDER_REVIEW, reviewer, reason, submitted_at, "submitted_for_review")


def return_corpus_case_to_draft(record: CorpusGovernanceRecord, *, reviewer: str, reason: str, returned_at: str) -> CorpusGovernanceRecord:
    return _transition(record, CorpusLifecycle.DRAFT, reviewer, reason, returned_at, "returned_to_draft")


def approve_corpus_case(
    record: CorpusGovernanceRecord,
    *,
    approved_final_translation: str,
    source_text: str,
    human_approver: str,
    approval_reason: str,
    approved_at: str,
    approval_source: str,
    decision: HumanReviewDecision,
    source_artifact: str,
    decision_artifacts: dict[str, str],
) -> CorpusGovernanceRecord:
    validate_human_actor(human_approver)
    validate_lifecycle_transition(record.status, CorpusLifecycle.APPROVED)
    if record.status is not CorpusLifecycle.UNDER_REVIEW:
        raise ValueError("only an under_review case can be approved")
    if approval_source != APPROVAL_SOURCE:
        raise ValueError("approval source must be human_governance_review")
    if decision.decision is not ReviewDecisionStatus.ACCEPTED:
        raise ValueError("an accepted Stage 11.5 decision is an approval prerequisite")
    translation = approved_final_translation.strip()
    if not translation:
        raise ValueError("approved translation is required")
    if translation == source_text.strip():
        raise ValueError("approved translation must differ from source text")
    verify_corpus_integrity(record, source_artifact=source_artifact, source_text=source_text, decision=decision, decision_artifacts=decision_artifacts)
    approval = ApprovalProvenance(
        human_approver, approval_reason, approved_at, approval_source, decision.decision_id,
        record.source_evidence.source_text_sha256, sha256_text(translation),
        decision.review_artifact_sha256, decision.metrics_sha256, decision.defects_sha256,
        GOVERNANCE_SCHEMA_VERSION,
    )
    updated = replace(record, status=CorpusLifecycle.APPROVED, approved_final_translation=translation, approval=approval, audit_history=_event(record, "approved", human_approver, approval_reason, approved_at, CorpusLifecycle.APPROVED))
    return validate_governance_record(updated)


def reject_corpus_case(record: CorpusGovernanceRecord, *, rejected_by: str, rejection_reason: str, rejected_at: str) -> CorpusGovernanceRecord:
    validate_human_actor(rejected_by)
    validate_lifecycle_transition(record.status, CorpusLifecycle.REJECTED)
    metadata = RejectionMetadata(rejected_at, rejected_by, rejection_reason)
    updated = replace(record, status=CorpusLifecycle.REJECTED, rejection=metadata, approved_final_translation=None, approval=None, audit_history=_event(record, "rejected", rejected_by, rejection_reason, rejected_at, CorpusLifecycle.REJECTED))
    return validate_governance_record(updated)


def supersede_corpus_case(record: CorpusGovernanceRecord, *, superseded_by: CorpusGovernanceRecord, human_approver: str, supersession_reason: str, superseded_at: str) -> CorpusGovernanceRecord:
    validate_human_actor(human_approver)
    validate_lifecycle_transition(record.status, CorpusLifecycle.SUPERSEDED)
    if superseded_by.status is not CorpusLifecycle.APPROVED or superseded_by.case_id == record.case_id:
        raise ValueError("supersession target must be a different approved case")
    metadata = SupersessionMetadata(superseded_by.case_id, superseded_at, supersession_reason, human_approver)
    updated = replace(record, status=CorpusLifecycle.SUPERSEDED, supersession=metadata, audit_history=_event(record, "superseded", human_approver, supersession_reason, superseded_at, CorpusLifecycle.SUPERSEDED))
    return validate_governance_record(updated)


def deprecate_corpus_case(record: CorpusGovernanceRecord, *, deprecated_by: str, deprecation_reason: str, deprecated_at: str) -> CorpusGovernanceRecord:
    validate_human_actor(deprecated_by)
    validate_lifecycle_transition(record.status, CorpusLifecycle.DEPRECATED)
    metadata = DeprecationMetadata(deprecated_at, deprecated_by, deprecation_reason)
    updated = replace(record, status=CorpusLifecycle.DEPRECATED, deprecation=metadata, audit_history=_event(record, "deprecated", deprecated_by, deprecation_reason, deprecated_at, CorpusLifecycle.DEPRECATED))
    return validate_governance_record(updated)


def create_case_revision(record: CorpusGovernanceRecord, *, changed_by: str, change_reason: str, changed_at: str) -> CorpusGovernanceRecord:
    validate_human_actor(changed_by)
    if record.status is CorpusLifecycle.DEPRECATED:
        raise ValueError("deprecated case cannot be revised")
    number = record.revision_number + 1
    revision_id = record.revision_id.rsplit("-R", 1)[0] + f"-R{number:03d}"
    event = AuditEvent("revision_created", changed_by, change_reason, changed_at, record.status.value, CorpusLifecycle.DRAFT.value)
    revised = replace(record, revision_id=revision_id, revision_number=number, previous_revision_id=record.revision_id, status=CorpusLifecycle.DRAFT, approved_final_translation=None, approval=None, supersession=None, deprecation=None, rejection=None, audit_history=record.audit_history + (event,))
    return validate_governance_record(revised)


from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .lifecycle import CorpusLifecycle


@dataclass(frozen=True)
class SourceEvidence:
    source_text_excerpt: str | None
    source_language: str
    target_language: str
    source_text_sha256: str
    source_artifact_reference: str
    source_artifact_sha256: str
    created_at: str
    schema_version: str


@dataclass(frozen=True)
class ApprovalProvenance:
    human_approver: str
    approval_reason: str
    approved_at: str
    approval_source: str
    approval_decision_id: str
    source_text_sha256: str
    approved_translation_sha256: str
    review_artifact_sha256: str
    metrics_sha256: str
    defects_sha256: str
    governance_schema_version: str


@dataclass(frozen=True)
class SupersessionMetadata:
    superseded_by_case_id: str
    superseded_at: str
    supersession_reason: str
    human_approver: str


@dataclass(frozen=True)
class DeprecationMetadata:
    deprecated_at: str
    deprecated_by: str
    deprecation_reason: str


@dataclass(frozen=True)
class RejectionMetadata:
    rejected_at: str
    rejected_by: str
    rejection_reason: str


@dataclass(frozen=True)
class AuditEvent:
    action: str
    actor: str
    reason: str
    occurred_at: str
    from_status: str | None
    to_status: str


@dataclass(frozen=True)
class CorpusGovernanceRecord:
    case_id: str
    revision_id: str
    revision_number: int
    previous_revision_id: str | None
    status: CorpusLifecycle
    source_evidence: SourceEvidence
    approved_final_translation: str | None
    approval: ApprovalProvenance | None
    supersession: SupersessionMetadata | None
    deprecation: DeprecationMetadata | None
    rejection: RejectionMetadata | None
    audit_history: tuple[AuditEvent, ...]
    governance_schema_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "audit_history", tuple(self.audit_history))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["audit_history"] = [asdict(event) for event in self.audit_history]
        return payload


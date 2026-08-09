"""RM-7.3.2 P4 Entity Consistency Review — core domain models.

Detect → Report → Review → Accept → Learn
No auto-learning. No provider. No network. No translation engine dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.entity_consistency.models import EntityMismatch
from core.knowledge_evolution.models import EntityType, Severity


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CandidateOrigin(str, Enum):
    """Origin of the review candidate."""
    ENTITY_CONSISTENCY = "ENTITY_CONSISTENCY"


class ReviewStatus(str, Enum):
    """Review candidate lifecycle status."""
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class FormType(str, Enum):
    """Name form types from entity normalization."""
    FULL_NAME = "FULL_NAME"
    GIVEN_NAME = "GIVEN_NAME"
    FAMILY_NAME = "FAMILY_NAME"
    NICKNAME = "NICKNAME"
    TITLE = "TITLE"
    FORMAL = "FORMAL"
    INTIMATE = "INTIMATE"
    RELATIONSHIP = "RELATIONSHIP"


@dataclass(frozen=True)
class Evidence:
    """Structured evidence for a review candidate.
    
    Must be reproducible — answers "why was this flagged as a problem?"
    """
    rule: str
    source_chunk: str
    position: Optional[int] = None
    policy_form_type: Optional[FormType] = None
    forbidden_pattern: Optional[str] = None
    allowed_pattern: Optional[str] = None
    match_result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "source_chunk": self.source_chunk,
            "position": self.position,
            "policy_form_type": self.policy_form_type.value if self.policy_form_type else None,
            "forbidden_pattern": self.forbidden_pattern,
            "allowed_pattern": self.allowed_pattern,
            "match_result": self.match_result,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            rule=str(data["rule"]),
            source_chunk=str(data["source_chunk"]),
            position=data.get("position"),
            policy_form_type=FormType(str(data["policy_form_type"])) if data.get("policy_form_type") else None,
            forbidden_pattern=data.get("forbidden_pattern"),
            allowed_pattern=data.get("allowed_pattern"),
            match_result=data.get("match_result"),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_mismatch(cls, mismatch: EntityMismatch, form_type: Optional[FormType] = None,
                      policy_detail: Optional[Dict[str, Any]] = None) -> "Evidence":
        """Create evidence from an EntityMismatch."""
        metadata = dict(mismatch.metadata)
        if policy_detail:
            metadata.update(policy_detail)
        return cls(
            rule=metadata.get("match_rule", "ENTITY_CONSISTENCY_MISMATCH"),
            source_chunk=mismatch.source,
            position=mismatch.position,
            policy_form_type=form_type,
            forbidden_pattern=metadata.get("forbidden_pattern"),
            allowed_pattern=metadata.get("allowed_pattern"),
            match_result=metadata.get("match_result"),
            metadata=metadata,
        )


@dataclass(frozen=True)
class ReviewCandidate:
    """A candidate for human review generated from consistency mismatches.
    
    Cannot directly modify glossary/knowledge base. Must be reviewed first.
    """
    candidate_id: str
    entity_id: str
    entity_type: EntityType
    source_form: str
    form_type: FormType
    expected_translation: str
    actual_translation: str
    severity: Severity
    match_status: str
    source_location: str
    evidence: Evidence
    origin: CandidateOrigin = CandidateOrigin.ENTITY_CONSISTENCY
    status: ReviewStatus = ReviewStatus.OPEN
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "source_form": self.source_form,
            "form_type": self.form_type.value,
            "expected_translation": self.expected_translation,
            "actual_translation": self.actual_translation,
            "severity": self.severity.value,
            "match_status": self.match_status,
            "source_location": self.source_location,
            "evidence": self.evidence.to_dict(),
            "origin": self.origin.value,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewCandidate":
        return cls(
            candidate_id=str(data["candidate_id"]),
            entity_id=str(data["entity_id"]),
            entity_type=EntityType(str(data["entity_type"])),
            source_form=str(data["source_form"]),
            form_type=FormType(str(data["form_type"])),
            expected_translation=str(data["expected_translation"]),
            actual_translation=str(data["actual_translation"]),
            severity=Severity(str(data["severity"])),
            match_status=str(data["match_status"]),
            source_location=str(data["source_location"]),
            evidence=Evidence.from_dict(data["evidence"]),
            origin=CandidateOrigin(str(data.get("origin", "ENTITY_CONSISTENCY"))),
            status=ReviewStatus(str(data.get("status", "OPEN"))),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
        )

    def with_status(self, new_status: ReviewStatus) -> "ReviewCandidate":
        """Return a new candidate with updated status."""
        return ReviewCandidate(
            candidate_id=self.candidate_id,
            entity_id=self.entity_id,
            entity_type=self.entity_type,
            source_form=self.source_form,
            form_type=self.form_type,
            expected_translation=self.expected_translation,
            actual_translation=self.actual_translation,
            severity=self.severity,
            match_status=self.match_status,
            source_location=self.source_location,
            evidence=self.evidence,
            origin=self.origin,
            status=new_status,
            metadata=dict(self.metadata),
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )


@dataclass(frozen=True)
class KnowledgeEvolutionCandidate:
    """Bridge candidate for Knowledge Evolution system.
    
    Created ONLY after ReviewCandidate is ACCEPTED.
    Preserves full provenance chain.
    """
    source_candidate_id: str
    entity_id: str
    entity_type: EntityType
    form_type: FormType
    source_form: str
    expected_translation: str
    actual_translation: str
    evidence: Evidence
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_candidate_id": self.source_candidate_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "form_type": self.form_type.value,
            "source_form": self.source_form,
            "expected_translation": self.expected_translation,
            "actual_translation": self.actual_translation,
            "evidence": self.evidence.to_dict(),
            "provenance": dict(self.provenance),
            "created_at": self.created_at,
        }

    @classmethod
    def from_review_candidate(cls, candidate: ReviewCandidate) -> "KnowledgeEvolutionCandidate":
        """Create KE candidate from an ACCEPTED ReviewCandidate."""
        if candidate.status != ReviewStatus.ACCEPTED:
            raise ValueError("Only ACCEPTED candidates can become KnowledgeEvolutionCandidate")
        return cls(
            source_candidate_id=candidate.candidate_id,
            entity_id=candidate.entity_id,
            entity_type=candidate.entity_type,
            form_type=candidate.form_type,
            source_form=candidate.source_form,
            expected_translation=candidate.expected_translation,
            actual_translation=candidate.actual_translation,
            evidence=candidate.evidence,
            provenance={
                "source": candidate.origin.value,
                "review_status": candidate.status.value,
                "reviewed_at": candidate.updated_at,
                "original_metadata": dict(candidate.metadata),
            },
        )


__all__ = [
    "CandidateOrigin",
    "ReviewStatus",
    "FormType",
    "Evidence",
    "ReviewCandidate",
    "KnowledgeEvolutionCandidate",
]
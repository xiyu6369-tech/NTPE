from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "2.0"
DEFAULT_PROMPT_TOKEN_BUDGET = 256
MAX_EVIDENCE_EXCERPT_CHARS = 512


class FactType(str, Enum):
    CANONICAL_NAME = "canonical_name"
    NAME_VARIANT = "name_variant"
    PRONOUN_OR_GENDER_REFERENCE = "pronoun_or_gender_reference"
    ROLE_OR_IDENTITY = "role_or_identity"
    RELATIONSHIP = "relationship"
    ADDRESSING_STYLE = "addressing_style"
    SPEECH_STYLE = "speech_style"
    PERSONALITY_TRAIT = "personality_trait"
    APPEARANCE = "appearance"
    TEMPORAL_STATE = "temporal_state"
    LOCATION_STATE = "location_state"
    TERMINOLOGY_PREFERENCE = "terminology_preference"
    OTHER = "other"


class EvidenceType(str, Enum):
    SOURCE_OBSERVATION = "source_observation"
    TRANSLATION_OBSERVATION = "translation_observation"
    AI_INFERENCE = "ai_inference"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    HISTORICAL_IMPORT = "historical_import"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MemoryStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"
    INVALID = "invalid"


class ExpiryKind(str, Enum):
    NEVER = "never"
    SEGMENT_SCOPE = "segment_scope"
    CHAPTER_SCOPE = "chapter_scope"
    SESSION_SCOPE = "session_scope"
    TIMESTAMP = "timestamp"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class AddDisposition(str, Enum):
    ACCEPTED = "accepted"
    MERGED = "merged"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: EvidenceType
    source_case_id: str
    source_segment_id: str
    source_text_hash: str
    excerpt: str
    language: str
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "source_case_id": self.source_case_id,
            "source_segment_id": self.source_segment_id,
            "source_text_hash": self.source_text_hash,
            "excerpt": self.excerpt,
            "language": self.language,
            "observed_at": self.observed_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Evidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            evidence_type=EvidenceType(str(data["evidence_type"])),
            source_case_id=str(data["source_case_id"]),
            source_segment_id=str(data["source_segment_id"]),
            source_text_hash=str(data["source_text_hash"]),
            excerpt=str(data["excerpt"]),
            language=str(data["language"]),
            observed_at=str(data["observed_at"]),
        )


@dataclass(frozen=True)
class ApprovalMetadata:
    approved_value: str
    approved_at: str
    reviewer: str | None = None
    decision_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved_value": self.approved_value,
            "approved_at": self.approved_at,
            "reviewer": self.reviewer,
            "decision_reference": self.decision_reference,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApprovalMetadata":
        return cls(
            approved_value=str(data["approved_value"]),
            approved_at=str(data["approved_at"]),
            reviewer=None if data.get("reviewer") is None else str(data["reviewer"]),
            decision_reference=None if data.get("decision_reference") is None else str(data["decision_reference"]),
        )


@dataclass(frozen=True)
class ExpiryPolicy:
    kind: ExpiryKind
    scope_id: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "scope_id": self.scope_id, "expires_at": self.expires_at}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpiryPolicy":
        return cls(
            kind=ExpiryKind(str(data["kind"])),
            scope_id=None if data.get("scope_id") is None else str(data["scope_id"]),
            expires_at=None if data.get("expires_at") is None else str(data["expires_at"]),
        )


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    character_id: str
    fact_type: FactType
    value: str
    evidence: tuple[Evidence, ...]
    evidence_type: EvidenceType
    confidence: float
    approval_status: ApprovalStatus
    source_language: str
    source_case_id: str
    source_segment_id: str
    created_at: str
    updated_at: str
    version: int
    expiry_policy: ExpiryPolicy
    status: MemoryStatus
    approval_metadata: ApprovalMetadata | None = None
    unresolved_identity: bool = False
    supersedes_memory_id: str | None = None

    def with_changes(self, **changes: Any) -> "MemoryRecord":
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "character_id": self.character_id,
            "fact_type": self.fact_type.value,
            "value": self.value,
            "evidence": [item.to_dict() for item in self.evidence],
            "evidence_type": self.evidence_type.value,
            "confidence": self.confidence,
            "approval_status": self.approval_status.value,
            "source_language": self.source_language,
            "source_case_id": self.source_case_id,
            "source_segment_id": self.source_segment_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "expiry_policy": self.expiry_policy.to_dict(),
            "status": self.status.value,
            "approval_metadata": None if self.approval_metadata is None else self.approval_metadata.to_dict(),
            "unresolved_identity": self.unresolved_identity,
            "supersedes_memory_id": self.supersedes_memory_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryRecord":
        approval = data.get("approval_metadata")
        return cls(
            memory_id=str(data["memory_id"]),
            character_id=str(data["character_id"]),
            fact_type=FactType(str(data["fact_type"])),
            value=str(data["value"]),
            evidence=tuple(Evidence.from_dict(item) for item in data["evidence"]),
            evidence_type=EvidenceType(str(data["evidence_type"])),
            confidence=float(data["confidence"]),
            approval_status=ApprovalStatus(str(data["approval_status"])),
            source_language=str(data["source_language"]),
            source_case_id=str(data["source_case_id"]),
            source_segment_id=str(data["source_segment_id"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            version=int(data["version"]),
            expiry_policy=ExpiryPolicy.from_dict(data["expiry_policy"]),
            status=MemoryStatus(str(data["status"])),
            approval_metadata=None if approval is None else ApprovalMetadata.from_dict(approval),
            unresolved_identity=bool(data.get("unresolved_identity", False)),
            supersedes_memory_id=None if data.get("supersedes_memory_id") is None else str(data["supersedes_memory_id"]),
        )


@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    character_id: str
    fact_type: FactType
    memory_ids: tuple[str, ...]
    created_at: str
    resolution: str | None = None
    preferred_memory_id: str | None = None

    @property
    def unresolved(self) -> bool:
        return self.resolution is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "character_id": self.character_id,
            "fact_type": self.fact_type.value,
            "memory_ids": list(self.memory_ids),
            "created_at": self.created_at,
            "resolution": self.resolution,
            "preferred_memory_id": self.preferred_memory_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConflictRecord":
        return cls(
            conflict_id=str(data["conflict_id"]),
            character_id=str(data["character_id"]),
            fact_type=FactType(str(data["fact_type"])),
            memory_ids=tuple(str(item) for item in data["memory_ids"]),
            created_at=str(data["created_at"]),
            resolution=None if data.get("resolution") is None else str(data["resolution"]),
            preferred_memory_id=None if data.get("preferred_memory_id") is None else str(data["preferred_memory_id"]),
        )


@dataclass(frozen=True)
class AddResult:
    disposition: AddDisposition
    record: MemoryRecord
    conflict: ConflictRecord | None = None
    message: str = ""


@dataclass(frozen=True)
class PromptMemoryItem:
    memory_id: str
    character_id: str
    fact_type: FactType
    value: str
    evidence_ids: tuple[str, ...]
    estimated_tokens: int
    priority: int


@dataclass(frozen=True)
class SelectionResult:
    items: tuple[PromptMemoryItem, ...] = field(default_factory=tuple)
    token_budget: int = DEFAULT_PROMPT_TOKEN_BUDGET
    estimated_tokens: int = 0
    excluded_counts: Mapping[str, int] = field(default_factory=dict)


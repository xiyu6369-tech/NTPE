from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
DEFAULT_CONTEXT_TOKEN_BUDGET = 512
DEFAULT_CHARACTER_TOKEN_BUDGET = 256
MAX_CONTEXT_EXCERPT_CHARS = 512
MAX_CONTEXT_VALUE_CHARS = 1024


class ContextType(str, Enum):
    PREVIOUS_TRANSLATION_EXCERPT = "previous_translation_excerpt"
    SOURCE_CONTEXT_EXCERPT = "source_context_excerpt"
    SCENE_SUMMARY = "scene_summary"
    EVENT_STATE = "event_state"
    TEMPORAL_STATE = "temporal_state"
    LOCATION_STATE = "location_state"
    SPEAKER_STATE = "speaker_state"
    POINT_OF_VIEW = "point_of_view"
    RELATIONSHIP_STATE = "relationship_state"
    ADDRESSING_STATE = "addressing_state"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    TERMINOLOGY_STATE = "terminology_state"
    CONTINUITY_NOTE = "continuity_note"
    OTHER = "other"


class EvidenceType(str, Enum):
    SOURCE_OBSERVATION = "source_observation"
    TRANSLATION_OBSERVATION = "translation_observation"
    RULE_DERIVED = "rule_derived"
    AI_INFERENCE = "ai_inference"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    HISTORICAL_IMPORT = "historical_import"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RecordStatus(str, Enum):
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
    SCENE_SCOPE = "scene_scope"
    CHAPTER_SCOPE = "chapter_scope"
    SESSION_SCOPE = "session_scope"
    TIMESTAMP = "timestamp"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class BoundaryType(str, Enum):
    SAME_SCENE = "same_scene"
    SCENE_TRANSITION = "scene_transition"
    CHAPTER_TRANSITION = "chapter_transition"
    UNKNOWN_TRANSITION = "unknown_transition"
    MANUAL_BOUNDARY = "manual_boundary"


class ParticipantStatus(str, Enum):
    PRESENT = "present"
    MENTIONED = "mentioned"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    EXITED_SCENE = "exited_scene"


class ResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    CANDIDATE = "candidate"
    RESOLVED = "resolved"
    HUMAN_APPROVED = "human_approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AddDisposition(str, Enum):
    ACCEPTED = "accepted"
    MERGED = "merged"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


@dataclass(frozen=True)
class ContextEvidence:
    evidence_id: str
    evidence_type: EvidenceType
    source_case_id: str
    source_segment_id: str
    source_text_hash: str | None
    translation_text_hash: str | None
    excerpt: str
    language: str
    rule_id: str | None
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, "evidence_type": self.evidence_type.value, "source_case_id": self.source_case_id, "source_segment_id": self.source_segment_id, "source_text_hash": self.source_text_hash, "translation_text_hash": self.translation_text_hash, "excerpt": self.excerpt, "language": self.language, "rule_id": self.rule_id, "observed_at": self.observed_at}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContextEvidence":
        return cls(str(data["evidence_id"]), EvidenceType(str(data["evidence_type"])), str(data["source_case_id"]), str(data["source_segment_id"]), None if data.get("source_text_hash") is None else str(data["source_text_hash"]), None if data.get("translation_text_hash") is None else str(data["translation_text_hash"]), str(data["excerpt"]), str(data["language"]), None if data.get("rule_id") is None else str(data["rule_id"]), str(data["observed_at"]))


@dataclass(frozen=True)
class ExpiryPolicy:
    kind: ExpiryKind
    scope_id: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "scope_id": self.scope_id, "expires_at": self.expires_at}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpiryPolicy":
        return cls(ExpiryKind(str(data["kind"])), None if data.get("scope_id") is None else str(data["scope_id"]), None if data.get("expires_at") is None else str(data["expires_at"]))


@dataclass(frozen=True)
class ContextMemoryRecord:
    context_id: str
    context_type: ContextType
    value: str
    evidence: tuple[ContextEvidence, ...]
    confidence: float
    approval_status: ApprovalStatus
    source_language: str
    source_case_id: str
    source_segment_id: str
    chapter_id: str | None
    scene_id: str | None
    sequence_index: int
    scope: str
    created_at: str
    updated_at: str
    version: int
    expiry_policy: ExpiryPolicy
    status: RecordStatus
    supersedes_context_id: str | None = None
    experimental_only: bool = False

    def with_changes(self, **changes: Any) -> "ContextMemoryRecord":
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {"context_id": self.context_id, "context_type": self.context_type.value, "value": self.value, "evidence": [item.to_dict() for item in self.evidence], "confidence": self.confidence, "approval_status": self.approval_status.value, "source_language": self.source_language, "source_case_id": self.source_case_id, "source_segment_id": self.source_segment_id, "chapter_id": self.chapter_id, "scene_id": self.scene_id, "sequence_index": self.sequence_index, "scope": self.scope, "created_at": self.created_at, "updated_at": self.updated_at, "version": self.version, "expiry_policy": self.expiry_policy.to_dict(), "status": self.status.value, "supersedes_context_id": self.supersedes_context_id, "experimental_only": self.experimental_only}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContextMemoryRecord":
        return cls(str(data["context_id"]), ContextType(str(data["context_type"])), str(data["value"]), tuple(ContextEvidence.from_dict(item) for item in data["evidence"]), float(data["confidence"]), ApprovalStatus(str(data["approval_status"])), str(data["source_language"]), str(data["source_case_id"]), str(data["source_segment_id"]), None if data.get("chapter_id") is None else str(data["chapter_id"]), None if data.get("scene_id") is None else str(data["scene_id"]), int(data["sequence_index"]), str(data["scope"]), str(data["created_at"]), str(data["updated_at"]), int(data["version"]), ExpiryPolicy.from_dict(data["expiry_policy"]), RecordStatus(str(data["status"])), None if data.get("supersedes_context_id") is None else str(data["supersedes_context_id"]), bool(data.get("experimental_only", False)))


@dataclass(frozen=True)
class SceneParticipant:
    character_id: str
    memory_version: int | None
    participant_status: ParticipantStatus
    presence_confidence: float
    evidence_reference: str
    unresolved_identity: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"character_id": self.character_id, "memory_version": self.memory_version, "participant_status": self.participant_status.value, "presence_confidence": self.presence_confidence, "evidence_reference": self.evidence_reference, "unresolved_identity": self.unresolved_identity}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SceneParticipant":
        return cls(str(data["character_id"]), None if data.get("memory_version") is None else int(data["memory_version"]), ParticipantStatus(str(data["participant_status"])), float(data["presence_confidence"]), str(data["evidence_reference"]), bool(data.get("unresolved_identity", False)))


@dataclass(frozen=True)
class UnresolvedReference:
    reference_id: str
    surface_form: str
    reference_type: str
    candidate_targets: tuple[str, ...]
    evidence: tuple[ContextEvidence, ...]
    confidence: float
    resolution_status: ResolutionStatus
    scope: str
    expiry: ExpiryPolicy
    resolved_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"reference_id": self.reference_id, "surface_form": self.surface_form, "reference_type": self.reference_type, "candidate_targets": list(self.candidate_targets), "evidence": [item.to_dict() for item in self.evidence], "confidence": self.confidence, "resolution_status": self.resolution_status.value, "scope": self.scope, "expiry": self.expiry.to_dict(), "resolved_target": self.resolved_target}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "UnresolvedReference":
        return cls(str(data["reference_id"]), str(data["surface_form"]), str(data["reference_type"]), tuple(str(item) for item in data["candidate_targets"]), tuple(ContextEvidence.from_dict(item) for item in data["evidence"]), float(data["confidence"]), ResolutionStatus(str(data["resolution_status"])), str(data["scope"]), ExpiryPolicy.from_dict(data["expiry"]), None if data.get("resolved_target") is None else str(data["resolved_target"]))


@dataclass(frozen=True)
class SceneMemoryRecord:
    scene_id: str
    scene_version: int
    chapter_id: str
    location: str | None
    time_state: str | None
    participants: tuple[SceneParticipant, ...]
    active_speaker: str | None
    point_of_view: str | None
    event_state: tuple[str, ...]
    unresolved_references: tuple[UnresolvedReference, ...]
    evidence: tuple[ContextEvidence, ...]
    created_at: str
    updated_at: str
    status: RecordStatus

    def to_dict(self) -> dict[str, Any]:
        return {"scene_id": self.scene_id, "scene_version": self.scene_version, "chapter_id": self.chapter_id, "location": self.location, "time_state": self.time_state, "participants": [item.to_dict() for item in self.participants], "active_speaker": self.active_speaker, "point_of_view": self.point_of_view, "event_state": list(self.event_state), "unresolved_references": [item.to_dict() for item in self.unresolved_references], "evidence": [item.to_dict() for item in self.evidence], "created_at": self.created_at, "updated_at": self.updated_at, "status": self.status.value}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SceneMemoryRecord":
        return cls(str(data["scene_id"]), int(data["scene_version"]), str(data["chapter_id"]), None if data.get("location") is None else str(data["location"]), None if data.get("time_state") is None else str(data["time_state"]), tuple(SceneParticipant.from_dict(item) for item in data["participants"]), None if data.get("active_speaker") is None else str(data["active_speaker"]), None if data.get("point_of_view") is None else str(data["point_of_view"]), tuple(str(item) for item in data["event_state"]), tuple(UnresolvedReference.from_dict(item) for item in data["unresolved_references"]), tuple(ContextEvidence.from_dict(item) for item in data["evidence"]), str(data["created_at"]), str(data["updated_at"]), RecordStatus(str(data["status"])))


@dataclass(frozen=True)
class AddResult:
    disposition: AddDisposition
    record: ContextMemoryRecord
    conflicting_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelectedContextItem:
    item_id: str
    item_type: str
    value: str
    evidence_ids: tuple[str, ...]
    estimated_tokens: int
    priority: int


@dataclass(frozen=True)
class CharacterContextItem:
    memory_id: str
    character_id: str
    fact_type: str
    value: str
    evidence_ids: tuple[str, ...]
    estimated_tokens: int


@dataclass(frozen=True)
class ContextSelectionResult:
    selected_records: tuple[SelectedContextItem, ...]
    selected_character_memories: tuple[CharacterContextItem, ...]
    estimated_tokens: int
    character_estimated_tokens: int
    budget: int
    character_budget: int
    dropped_records: tuple[str, ...]
    drop_reasons: Mapping[str, tuple[str, ...]]
    deterministic_fingerprint: str


"""RM-7.0 Knowledge Evolution Foundation — core domain models.

No provider imports. No network. No translation engine dependencies.
Completely offline knowledge lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntityType(Enum):
    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    TERM = "TERM"
    TITLE = "TITLE"
    ALIAS = "ALIAS"


class PriorityLevel(Enum):
    USER = "USER"
    RUNTIME = "RUNTIME"
    LEARNING = "LEARNING"
    AUTO = "AUTO"

    def compare_ordinal(self) -> int:
        return PRIORITY_ORDER.index(self)

    def __lt__(self, other: "PriorityLevel") -> bool:
        return self.compare_ordinal() < other.compare_ordinal()

    def __le__(self, other: "PriorityLevel") -> bool:
        return self.compare_ordinal() <= other.compare_ordinal()


PRIORITY_ORDER: List[PriorityLevel] = [
    PriorityLevel.USER,
    PriorityLevel.RUNTIME,
    PriorityLevel.LEARNING,
    PriorityLevel.AUTO,
]


class Severity(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CandidateStatus(Enum):
    PENDING = "PENDING"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class KnowledgeEntity:
    source: str
    canonical: str
    entity_type: EntityType
    priority: PriorityLevel = PriorityLevel.LEARNING
    locked: bool = False
    entity_id: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    version: int = 1

    @property
    def is_locked(self) -> bool:
        return self.locked or self.priority == PriorityLevel.USER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "canonical": self.canonical,
            "entity_type": self.entity_type.value,
            "priority": self.priority.value,
            "locked": self.locked,
            "entity_id": self.entity_id,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntity":
        return cls(
            source=str(data["source"]),
            canonical=str(data["canonical"]),
            entity_type=EntityType(str(data["entity_type"])),
            priority=PriorityLevel(str(data["priority"])),
            locked=bool(data.get("locked", False)),
            entity_id=str(data.get("entity_id", "")),
            confidence=float(data.get("confidence", 1.0)),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
            version=int(data.get("version", 1)),
        )


@dataclass(frozen=True)
class AliasEntry:
    alias: str
    target: str
    confidence: float = 0.95
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alias": self.alias,
            "target": self.target,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AliasEntry":
        return cls(
            alias=str(data["alias"]),
            target=str(data["target"]),
            confidence=float(data.get("confidence", 0.95)),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class ConflictRecord:
    source: str
    expected: str
    observed: str
    severity: Severity = Severity.HIGH
    entity_type: EntityType = EntityType.CHARACTER
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    @property
    def resolved(self) -> bool:
        return self.resolution is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "expected": self.expected,
            "observed": self.observed,
            "severity": self.severity.value,
            "entity_type": self.entity_type.value,
            "resolution": self.resolution,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConflictRecord":
        return cls(
            source=str(data["source"]),
            expected=str(data["expected"]),
            observed=str(data["observed"]),
            severity=Severity(str(data.get("severity", "HIGH"))),
            entity_type=EntityType(str(data.get("entity_type", "CHARACTER"))),
            resolution=None if data.get("resolution") is None else str(data["resolution"]),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class EvolutionReport:
    new_entities: int = 0
    updated_entities: int = 0
    conflicts: int = 0
    promoted_candidates: int = 0
    rejected_candidates: int = 0
    total_entities: int = 0
    total_candidates: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    @property
    def has_changes(self) -> bool:
        return (
            self.new_entities > 0
            or self.updated_entities > 0
            or self.conflicts > 0
            or self.promoted_candidates > 0
            or self.rejected_candidates > 0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "new_entities": self.new_entities,
            "updated_entities": self.updated_entities,
            "conflicts": self.conflicts,
            "promoted_candidates": self.promoted_candidates,
            "rejected_candidates": self.rejected_candidates,
            "total_entities": self.total_entities,
            "total_candidates": self.total_candidates,
            "details": dict(self.details),
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionReport":
        return cls(
            new_entities=int(data.get("new_entities", 0)),
            updated_entities=int(data.get("updated_entities", 0)),
            conflicts=int(data.get("conflicts", 0)),
            promoted_candidates=int(data.get("promoted_candidates", 0)),
            rejected_candidates=int(data.get("rejected_candidates", 0)),
            total_entities=int(data.get("total_entities", 0)),
            total_candidates=int(data.get("total_candidates", 0)),
            details=dict(data.get("details", {})),
            generated_at=str(data.get("generated_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class LearningCandidate:
    source: str
    canonical: str
    entity_type: EntityType
    confidence: float = 0.5
    occurrence_count: int = 0
    context_hints: List[str] = field(default_factory=list)
    status: CandidateStatus = CandidateStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "canonical": self.canonical,
            "entity_type": self.entity_type.value,
            "confidence": self.confidence,
            "occurrence_count": self.occurrence_count,
            "context_hints": list(self.context_hints),
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningCandidate":
        return cls(
            source=str(data["source"]),
            canonical=str(data["canonical"]),
            entity_type=EntityType(str(data["entity_type"])),
            confidence=float(data.get("confidence", 0.5)),
            occurrence_count=int(data.get("occurrence_count", 0)),
            context_hints=list(data.get("context_hints", [])),
            status=CandidateStatus(str(data.get("status", "PENDING"))),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
        )
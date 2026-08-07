"""RM-7.1 Entity Consistency Runtime — domain models.

Pure dataclasses.  No provider imports.  No network.  No mutation.
Reuses EntityType and Severity from knowledge_evolution for source-of-truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.knowledge_evolution.models import EntityType, Severity


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntityCategory(str, Enum):
    """Coarse grouping used only for reporting."""
    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    TERM = "TERM"


class ReportSeverity(str, Enum):
    """Severity levels inside a consistency report."""
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"


ENTITY_TYPE_TO_CATEGORY: Dict[EntityType, EntityCategory] = {
    EntityType.CHARACTER:    EntityCategory.CHARACTER,
    EntityType.LOCATION:     EntityCategory.LOCATION,
    EntityType.ORGANIZATION: EntityCategory.ORGANIZATION,
    EntityType.TERM:         EntityCategory.TERM,
    EntityType.TITLE:        EntityCategory.TERM,
    EntityType.ALIAS:        EntityCategory.CHARACTER,
}

REPORTABLE_TYPES = frozenset(
    {EntityType.CHARACTER, EntityType.LOCATION, EntityType.ORGANIZATION, EntityType.TERM, EntityType.TITLE, EntityType.ALIAS}
)


@dataclass(frozen=True)
class EntityMatch:
    """A positive match: translation output uses the expected canonical form."""

    source: str
    expected: str
    found: str
    entity_type: EntityType
    category: EntityCategory = field(init=False)
    position: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", ENTITY_TYPE_TO_CATEGORY.get(self.entity_type, EntityCategory.TERM))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "expected": self.expected,
            "found": self.found,
            "entity_type": self.entity_type.value,
            "category": self.category.value,
            "position": self.position,
            "metadata": dict(self.metadata),
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityMatch":
        return cls(
            source=str(data["source"]),
            expected=str(data["expected"]),
            found=str(data["found"]),
            entity_type=EntityType(str(data["entity_type"])),
            position=data.get("position"),
            metadata=dict(data.get("metadata", {})),
            detected_at=str(data.get("detected_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class EntityMismatch:
    """A mismatch between the expected canonical form and what the translation actually contains."""

    source: str
    expected: str
    found: str
    entity_type: EntityType
    severity: Severity = Severity.HIGH
    position: Optional[int] = None
    knowledge_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=utc_now_iso)

    @property
    def category(self) -> EntityCategory:
        return ENTITY_TYPE_TO_CATEGORY.get(self.entity_type, EntityCategory.TERM)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "expected": self.expected,
            "found": self.found,
            "entity_type": self.entity_type.value,
            "severity": self.severity.value,
            "position": self.position,
            "knowledge_id": self.knowledge_id,
            "metadata": dict(self.metadata),
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityMismatch":
        return cls(
            source=str(data["source"]),
            expected=str(data["expected"]),
            found=str(data["found"]),
            entity_type=EntityType(str(data["entity_type"])),
            severity=Severity(str(data.get("severity", "HIGH"))),
            position=data.get("position"),
            knowledge_id=data.get("knowledge_id"),
            metadata=dict(data.get("metadata", {})),
            detected_at=str(data.get("detected_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class ConsistencyReport:
    """Aggregated output of a single consistency run."""

    total_scanned: int = 0
    matches: List[Dict[str, Any]] = field(default_factory=list)
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Dict[str, int]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    @property
    def pass_count(self) -> int:
        return len(self.matches)

    @property
    def mismatch_count(self) -> int:
        return len(self.mismatches)

    @property
    def all_pass(self) -> bool:
        return self.mismatch_count == 0

    def add_match(self, match: EntityMatch) -> "ConsistencyReport":
        return ConsistencyReport(
            total_scanned=self.total_scanned + 1,
            matches=self.matches + [match.to_dict()],
            mismatches=list(self.mismatches),
            summary=dict(self.summary),
            metadata=dict(self.metadata),
            generated_at=utc_now_iso(),
        )

    def add_mismatch(self, mismatch: EntityMismatch) -> "ConsistencyReport":
        return ConsistencyReport(
            total_scanned=self.total_scanned + 1,
            matches=list(self.matches),
            mismatches=self.mismatches + [mismatch.to_dict()],
            summary=dict(self.summary),
            metadata=dict(self.metadata),
            generated_at=utc_now_iso(),
        )

    def with_summary(self, summary: Dict[str, Dict[str, int]]) -> "ConsistencyReport":
        return ConsistencyReport(
            total_scanned=self.total_scanned,
            matches=list(self.matches),
            mismatches=list(self.mismatches),
            summary=dict(summary),
            metadata=dict(self.metadata),
            generated_at=utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scanned": self.total_scanned,
            "pass_count": self.pass_count,
            "mismatch_count": self.mismatch_count,
            "all_pass": self.all_pass,
            "matches": list(self.matches),
            "mismatches": list(self.mismatches),
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsistencyReport":
        return cls(
            total_scanned=int(data.get("total_scanned", 0)),
            matches=list(data.get("matches", [])),
            mismatches=list(data.get("mismatches", [])),
            summary=dict(data.get("summary", {})),
            metadata=dict(data.get("metadata", {})),
            generated_at=str(data.get("generated_at", utc_now_iso())),
        )
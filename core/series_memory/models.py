from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from core.character_memory_v2.models import (
    ApprovalStatus,
    Evidence,
    EvidenceType,
    FactType,
)


@dataclass(frozen=True)
class SeriesCharacterRecord:
    """Canonical character fact — NEVER expires, series-scoped."""
    series_character_id: str
    korean_name: str
    canonical_name: str
    aliases: Tuple[str, ...]
    fact_type: FactType
    value: str
    evidence: Tuple[Evidence, ...]
    confidence: float
    approval_status: ApprovalStatus
    source_books: Tuple[str, ...]
    created_at: str
    updated_at: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_character_id": self.series_character_id,
            "korean_name": self.korean_name,
            "canonical_name": self.canonical_name,
            "aliases": list(self.aliases),
            "fact_type": self.fact_type.value,
            "value": self.value,
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
            "approval_status": self.approval_status.value,
            "source_books": list(self.source_books),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SeriesCharacterRecord":
        return cls(
            series_character_id=str(data["series_character_id"]),
            korean_name=str(data["korean_name"]),
            canonical_name=str(data["canonical_name"]),
            aliases=tuple(str(item) for item in data.get("aliases", [])),
            fact_type=FactType(str(data["fact_type"])),
            value=str(data["value"]),
            evidence=tuple(Evidence.from_dict(item) for item in data.get("evidence", [])),
            confidence=float(data["confidence"]),
            approval_status=ApprovalStatus(str(data["approval_status"])),
            source_books=tuple(str(item) for item in data.get("source_books", [])),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            version=int(data["version"]),
        )


@dataclass(frozen=True)
class SeriesFactRecord:
    """Canonical non-character fact — NEVER expires, series-scoped."""
    series_fact_id: str
    fact_type: FactType
    value: str
    evidence: Tuple[Evidence, ...]
    confidence: float
    approval_status: ApprovalStatus
    source_books: Tuple[str, ...]
    created_at: str
    updated_at: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_fact_id": self.series_fact_id,
            "fact_type": self.fact_type.value,
            "value": self.value,
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
            "approval_status": self.approval_status.value,
            "source_books": list(self.source_books),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SeriesFactRecord":
        return cls(
            series_fact_id=str(data["series_fact_id"]),
            fact_type=FactType(str(data["fact_type"])),
            value=str(data["value"]),
            evidence=tuple(Evidence.from_dict(item) for item in data.get("evidence", [])),
            confidence=float(data["confidence"]),
            approval_status=ApprovalStatus(str(data["approval_status"])),
            source_books=tuple(str(item) for item in data.get("source_books", [])),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            version=int(data["version"]),
        )


@dataclass(frozen=True)
class AddResult:
    """Result of adding/merging a canonical fact."""
    disposition: str
    record: SeriesCharacterRecord | SeriesFactRecord
    conflict: "ConflictRecord | None" = None
    message: str = ""


@dataclass(frozen=True)
class ConflictRecord:
    """Record of a conflict between canonical facts."""
    conflict_id: str
    series_character_id: str
    fact_type: FactType
    record_ids: Tuple[str, ...]
    created_at: str
    resolution: str | None = None
    resolved_at: str | None = None
    resolved_by: str | None = None

    @property
    def unresolved(self) -> bool:
        return self.resolution is None


@dataclass(frozen=True)
class PromotionRecord:
    """Audit trail for Book → Series promotion."""
    promotion_id: str
    series_id: str
    book_identity: str
    source_memory_id: str
    target_series_character_id: str
    fact_type: FactType
    action: str
    resolved_by: str | None
    resolved_at: str
    previous_value: str | None
    new_value: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "source_memory_id": self.source_memory_id,
            "target_series_character_id": self.target_series_character_id,
            "fact_type": self.fact_type.value,
            "action": self.action,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
        }


@dataclass(frozen=True)
class HydrationReport:
    """Report of Series → Book hydration operation."""
    series_id: str
    book_identity: str
    hydrated_count: int
    skipped_count: int
    conflict_count: int
    hydration_source: str
    conflicts: Tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "hydrated_count": self.hydrated_count,
            "skipped_count": self.skipped_count,
            "conflict_count": self.conflict_count,
            "hydration_source": self.hydration_source,
            "conflicts": list(self.conflicts),
        }
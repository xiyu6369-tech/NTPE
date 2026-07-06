# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class SemanticUnit:
    unit_id: str
    text: str
    concepts: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    segment_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "text": self.text,
            "concepts": list(self.concepts),
            "events": list(self.events),
            "segment_id": self.segment_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SemanticFinding:
    category: str
    severity: str
    message: str
    concept: str | None = None
    segment_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "concept": self.concept,
            "segment_id": self.segment_id,
        }


@dataclass
class SemanticConsistencyResult:
    units: List[SemanticUnit] = field(default_factory=list)
    concept_map: Dict[str, List[str]] = field(default_factory=dict)
    event_map: Dict[str, List[str]] = field(default_factory=dict)
    contradictions: List[SemanticFinding] = field(default_factory=list)
    continuity_gaps: List[SemanticFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def unit_count(self) -> int:
        return len(self.units)

    @property
    def finding_count(self) -> int:
        return len(self.contradictions) + len(self.continuity_gaps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "units": [unit.to_dict() for unit in self.units],
            "concept_map": {k: list(v) for k, v in self.concept_map.items()},
            "event_map": {k: list(v) for k, v in self.event_map.items()},
            "contradictions": [item.to_dict() for item in self.contradictions],
            "continuity_gaps": [item.to_dict() for item in self.continuity_gaps],
            "metrics": dict(self.metrics),
        }

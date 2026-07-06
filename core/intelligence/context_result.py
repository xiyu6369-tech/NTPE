# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ContextItem:
    """A normalized context entry used by the intelligence layer."""

    item_id: str
    text: str
    priority: float = 1.0
    source: str = "runtime"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "text": self.text,
            "priority": float(self.priority),
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ContextEdge:
    source_id: str
    target_id: str
    relation: str = "sequence"
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": float(self.weight),
        }


@dataclass
class ContextIntelligenceResult:
    items: List[ContextItem] = field(default_factory=list)
    edges: List[ContextEdge] = field(default_factory=list)
    compressed_context: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "edges": [edge.to_dict() for edge in self.edges],
            "compressed_context": self.compressed_context,
            "metrics": dict(self.metrics),
        }

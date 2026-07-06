# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SemanticEdge:
    source: str
    target: str
    relation: str = "co_occurs"
    weight: float = 1.0

    def to_dict(self) -> Dict[str, object]:
        return {"source": self.source, "target": self.target, "relation": self.relation, "weight": float(self.weight)}


class SemanticGraph:
    def __init__(self) -> None:
        self.edges: List[SemanticEdge] = []

    def add_edge(self, source: str, target: str, relation: str = "co_occurs", weight: float = 1.0) -> SemanticEdge:
        edge = SemanticEdge(source=source, target=target, relation=relation, weight=weight)
        self.edges.append(edge)
        return edge

    def build_from_units(self, units) -> "SemanticGraph":
        for unit in units:
            concepts = list(unit.concepts)
            for left, right in zip(concepts, concepts[1:]):
                self.add_edge(left, right)
        return self

    def to_dict(self) -> Dict[str, object]:
        return {"edges": [edge.to_dict() for edge in self.edges]}

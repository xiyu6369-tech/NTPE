# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Dict, List, Set

from .character_relationship import CharacterRelationship


class CharacterGraph:
    """Small deterministic relationship graph for runtime-safe character tracking."""

    def __init__(self) -> None:
        self._nodes: Set[str] = set()
        self._edges: List[CharacterRelationship] = []

    def add_character(self, name: str) -> None:
        if name:
            self._nodes.add(name)

    def add_relationship(self, source: str, target: str, relation_type: str = "unknown", *, confidence: float = 1.0, **metadata: object) -> CharacterRelationship:
        self.add_character(source)
        self.add_character(target)
        relationship = CharacterRelationship(source, target, relation_type, confidence, dict(metadata))
        self._edges.append(relationship)
        return relationship

    def neighbors(self, name: str) -> List[str]:
        result: List[str] = []
        for edge in self._edges:
            if edge.source == name:
                result.append(edge.target)
            elif edge.target == name:
                result.append(edge.source)
        return result

    def relationships(self) -> List[CharacterRelationship]:
        return list(self._edges)

    def to_dict(self) -> Dict[str, object]:
        return {
            "characters": sorted(self._nodes),
            "relationships": [edge.to_dict() for edge in self._edges],
        }

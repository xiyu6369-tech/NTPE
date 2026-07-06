# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .context_result import ContextEdge, ContextItem


@dataclass
class ContextGraph:
    items: Dict[str, ContextItem] = field(default_factory=dict)
    edges: List[ContextEdge] = field(default_factory=list)

    def add_item(self, item: ContextItem) -> None:
        self.items[item.item_id] = item

    def add_edge(self, source_id: str, target_id: str, relation: str = "sequence", weight: float = 1.0) -> None:
        if source_id != target_id:
            self.edges.append(ContextEdge(source_id=source_id, target_id=target_id, relation=relation, weight=weight))

    def build_sequence(self, items: Iterable[ContextItem]) -> "ContextGraph":
        previous: ContextItem | None = None
        for item in items:
            self.add_item(item)
            if previous is not None:
                self.add_edge(previous.item_id, item.item_id)
            previous = item
        return self

    def to_edges(self) -> List[ContextEdge]:
        return list(self.edges)

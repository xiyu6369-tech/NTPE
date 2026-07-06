# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List


class SemanticMemory:
    """Small in-memory semantic trace for cross-chunk continuity."""

    def __init__(self) -> None:
        self.concepts: Counter[str] = Counter()
        self.events: Counter[str] = Counter()

    def observe_concepts(self, concepts: Iterable[str]) -> None:
        self.concepts.update(concepts)

    def observe_events(self, events: Iterable[str]) -> None:
        self.events.update(events)

    def top_concepts(self, limit: int = 10) -> List[str]:
        return [item for item, _count in self.concepts.most_common(limit)]

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        return {"concepts": dict(self.concepts), "events": dict(self.events)}

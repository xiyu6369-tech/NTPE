# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from typing import Iterable, Sequence

from .semantic_events import SEMANTIC_ANALYZED, SEMANTIC_COMPLETED, SEMANTIC_STARTED, SemanticEventBus
from .semantic_exceptions import SemanticInputError
from .semantic_graph import SemanticGraph
from .semantic_memory import SemanticMemory
from .semantic_pipeline import SemanticConsistencyPipeline
from .semantic_result import SemanticConsistencyResult


class SemanticConsistencyEngine:
    """Public Stage-16.4 facade for semantic consistency analysis."""

    stage = "Stage-16.4"
    name = "Semantic Consistency Engine"

    def __init__(self, *, event_bus: SemanticEventBus | None = None) -> None:
        self.event_bus = event_bus or SemanticEventBus()
        self.memory = SemanticMemory()
        self.graph = SemanticGraph()
        self.pipeline = SemanticConsistencyPipeline()

    def analyze_texts(self, texts: Sequence[str], *, source: str = "runtime") -> SemanticConsistencyResult:
        materialized = [text for text in texts if text and text.strip()]
        if not materialized:
            raise SemanticInputError("Semantic analysis text must not be empty.")
        self.event_bus.emit(SEMANTIC_STARTED, segment_count=len(materialized), source=source)
        result = self.pipeline.run(materialized, segment_prefix=source)
        for unit in result.units:
            self.memory.observe_concepts(unit.concepts)
            self.memory.observe_events(unit.events)
        self.graph.build_from_units(result.units)
        self.event_bus.emit(SEMANTIC_ANALYZED, unit_count=result.unit_count, finding_count=result.finding_count)
        self.event_bus.emit(SEMANTIC_COMPLETED, metrics=result.metrics)
        return result

    def analyze_text(self, text: str, *, source: str = "runtime") -> SemanticConsistencyResult:
        return self.analyze_texts([text], source=source)

    def analyze(self, texts: Iterable[str]) -> SemanticConsistencyResult:
        return self.analyze_texts(list(texts))

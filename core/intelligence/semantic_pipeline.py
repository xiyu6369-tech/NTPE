# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from typing import Sequence

from .semantic_metrics import build_semantic_metrics
from .semantic_result import SemanticConsistencyResult
from .semantic_rules import (
    build_concept_map,
    build_event_map,
    build_semantic_units,
    detect_continuity_gaps,
    detect_semantic_contradictions,
)


class SemanticConsistencyPipeline:
    """Deterministic semantic consistency pipeline for Stage-16.4."""

    def run(self, texts: Sequence[str], *, segment_prefix: str = "sem") -> SemanticConsistencyResult:
        units = build_semantic_units(texts, segment_prefix=segment_prefix)
        result = SemanticConsistencyResult(
            units=units,
            concept_map=build_concept_map(units),
            event_map=build_event_map(units),
            contradictions=detect_semantic_contradictions(units),
            continuity_gaps=detect_continuity_gaps(units),
        )
        result.metrics = build_semantic_metrics(result)
        return result

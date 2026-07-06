# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from typing import Any, Dict

from .semantic_result import SemanticConsistencyResult


def build_semantic_metrics(result: SemanticConsistencyResult) -> Dict[str, Any]:
    concept_count = len(result.concept_map)
    event_count = len(result.event_map)
    issue_count = result.finding_count
    consistency_score = max(0.0, 100.0 - (issue_count * 7.5))
    return {
        "unit_count": result.unit_count,
        "concept_count": concept_count,
        "event_count": event_count,
        "contradiction_count": len(result.contradictions),
        "continuity_gap_count": len(result.continuity_gaps),
        "semantic_consistency_score": round(consistency_score, 2),
    }

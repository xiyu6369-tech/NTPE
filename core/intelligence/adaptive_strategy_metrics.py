# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Sequence

from .adaptive_strategy_result import AdaptiveStrategyCandidate


def build_adaptive_strategy_metrics(candidates: Sequence[AdaptiveStrategyCandidate], selected_name: str) -> Dict[str, Any]:
    scores = [candidate.score for candidate in candidates]
    return {
        "candidate_count": len(candidates),
        "selected_strategy": selected_name,
        "best_score": max(scores) if scores else 0.0,
        "average_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
    }

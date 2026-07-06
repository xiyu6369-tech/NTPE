# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .adaptive_strategy_profile import AdaptiveStrategyProfile


@dataclass(frozen=True)
class AdaptiveStrategyCandidate:
    profile: AdaptiveStrategyProfile
    score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"profile": self.profile.to_dict(), "score": self.score, "reasons": list(self.reasons)}


@dataclass
class AdaptiveStrategyResult:
    selected: AdaptiveStrategyCandidate
    candidates: List[AdaptiveStrategyCandidate] = field(default_factory=list)
    content_type: str = "general"
    confidence: float = 0.0
    fallback_strategy: str = "balanced"
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def strategy_name(self) -> str:
        return self.selected.profile.name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "selected": self.selected.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "content_type": self.content_type,
            "confidence": self.confidence,
            "fallback_strategy": self.fallback_strategy,
            "metrics": dict(self.metrics),
        }

# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from .adaptive_strategy_profile import AdaptiveStrategyProfile, default_strategy_profiles


@dataclass
class AdaptiveStrategyPolicy:
    profiles: Dict[str, AdaptiveStrategyProfile] = field(default_factory=default_strategy_profiles)
    default_strategy: str = "balanced"
    minimum_confidence: float = 0.35
    prefer_quality_over_speed: bool = True

    def get_profiles(self) -> Iterable[AdaptiveStrategyProfile]:
        return self.profiles.values()

    def get_default(self) -> AdaptiveStrategyProfile:
        return self.profiles[self.default_strategy]

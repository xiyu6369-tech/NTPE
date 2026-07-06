# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class AdaptiveStrategyProfile:
    name: str
    content_types: List[str] = field(default_factory=list)
    priorities: Dict[str, float] = field(default_factory=dict)
    provider_hints: Dict[str, Any] = field(default_factory=dict)
    repair_hints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def priority(self, key: str, default: float = 0.0) -> float:
        return float(self.priorities.get(key, default))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content_types": list(self.content_types),
            "priorities": dict(self.priorities),
            "provider_hints": dict(self.provider_hints),
            "repair_hints": list(self.repair_hints),
            "metadata": dict(self.metadata),
        }


def default_strategy_profiles() -> Dict[str, AdaptiveStrategyProfile]:
    return {
        "balanced": AdaptiveStrategyProfile(
            name="balanced",
            content_types=["mixed", "general"],
            priorities={"fidelity": 0.7, "fluency": 0.7, "terminology": 0.6, "narrative": 0.6, "speed": 0.5},
            repair_hints=["quality_report", "terminology_check"],
        ),
        "novel_literary": AdaptiveStrategyProfile(
            name="novel_literary",
            content_types=["novel", "narrative"],
            priorities={"fidelity": 0.75, "fluency": 0.9, "narrative": 0.9, "character": 0.8, "speed": 0.3},
            repair_hints=["narrative_consistency", "character_consistency"],
        ),
        "dialogue_character": AdaptiveStrategyProfile(
            name="dialogue_character",
            content_types=["dialogue"],
            priorities={"fluency": 0.85, "character": 0.95, "terminology": 0.7, "narrative": 0.75, "speed": 0.4},
            repair_hints=["pronoun_resolution", "honorific_check"],
        ),
        "technical_precise": AdaptiveStrategyProfile(
            name="technical_precise",
            content_types=["technical", "list"],
            priorities={"fidelity": 0.95, "terminology": 0.95, "formatting": 0.85, "fluency": 0.55, "speed": 0.5},
            repair_hints=["placeholder_validation", "terminology_lock"],
        ),
        "speed_first": AdaptiveStrategyProfile(
            name="speed_first",
            content_types=["general"],
            priorities={"speed": 0.95, "fidelity": 0.55, "fluency": 0.55},
            repair_hints=["basic_quality_check"],
        ),
    }

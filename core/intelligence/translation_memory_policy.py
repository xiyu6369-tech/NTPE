# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationMemoryPolicy:
    min_score: float = 0.72
    exact_score: float = 1.0
    max_matches: int = 5
    prefer_same_domain: bool = True
    prefer_same_target_language: bool = True
    context_weight: float = 0.08
    terminology_weight: float = 0.08
    character_weight: float = 0.06

    def clamp_score(self, score: float) -> float:
        return max(0.0, min(1.0, score))

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityMetricsConfig:
    passing_score: float = 80.0
    blocking_overall_cap: float = 49.0
    neutral_score: float = 50.0

    def __post_init__(self) -> None:
        if not 0 <= self.blocking_overall_cap < self.passing_score <= 100:
            raise ValueError("quality metric thresholds invalid")

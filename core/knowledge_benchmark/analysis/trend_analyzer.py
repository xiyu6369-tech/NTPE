"""
Trend Analysis Engine (RM-5.8.4)

Analyzes multi-run trend data across RM-5.8.x milestones.
Detects Improving, Stable, Regression, or Insufficient Direction patterns
per extractor and metric over successive runs.

Offline. Deterministic. No external dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import TrendDirection, TrendResult


class TrendAnalyzer:
    """Analytics trend directions across multiple benchmark runs."""

    def analyze_all(
        self,
        run_histories: Dict[str, List[Dict[str, float]]],
        metric_names: Optional[List[str]] = None,
    ) -> List[TrendResult]:
        results: List[TrendResult] = []

        metric_names = metric_names or ["precision", "recall", "f1_score"]

        for extractor_name, run_values in run_histories.items():
            for metric_name in metric_names:
                values = []
                runs = []
                for run_data in run_values:
                    if metric_name in run_data:
                        values.append(float(run_data[metric_name]))
                        runs.append(run_data.get("run_id", ""))

                if len(values) < 2:
                    direction = TrendDirection.INSUFFICIENT_DATA
                elif len(values) == 2:
                    direction = self._trend_from_two(values)
                else:
                    direction = self._trend_from_sequence(values)

                results.append(TrendResult(
                    extractor_type=extractor_name,
                    metric_name=metric_name,
                    direction=direction,
                    values=values,
                    runs=runs,
                    details={
                        "run_count": len(runs),
                        "min_value": round(min(values), 4),
                        "max_value": round(max(values), 4),
                        "avg_improvement": round((values[-1] - values[0]) / max(1, len(values) - 1), 4),
                    },
                ))

        return results

    @staticmethod
    def _trend_from_two(values: List[float]) -> TrendDirection:
        if len(values) != 2:
            return TrendDirection.INSUFFICIENT_DATA

        delta = values[-1] - values[0]

        if abs(delta) < 0.005:
            return TrendDirection.STABLE
        if delta > 0:
            return TrendDirection.IMPROVING
        return TrendDirection.REGRESSION

    @staticmethod
    def _trend_from_sequence(values: List[float]) -> TrendDirection:
        if len(values) < 3:
            return TrendDirection.INSUFFICIENT_DATA

        fixed_window = 3 if len(values) >= 3 else len(values)
        check = values[-fixed_window:]

        is_increasing = all(
            check[i] <= check[i + 1] for i in range(len(check) - 1)
        ) and any(
            check[i] < check[i + 1] for i in range(len(check) - 1)
        )

        is_decreasing = all(
            check[i] >= check[i + 1] for i in range(len(check) - 1)
        ) and any(
            check[i] > check[i + 1] for i in range(len(check) - 1)
        )

        if is_increasing:
            return TrendDirection.IMPROVING
        if is_decreasing:
            return TrendDirection.REGRESSION

        early_avg = sum(values[:3]) / 3 if len(values) >= 3 else values[0]
        late_avg = sum(values[-3:]) / 3 if len(values) >= 3 else values[-1]

        if late_avg > early_avg + 0.01:
            return TrendDirection.IMPROVING
        elif late_avg < early_avg - 0.01:
            return TrendDirection.REGRESSION
        return TrendDirection.STABLE

    def analyze_for_extractor(
        self,
        extractor_name: str,
        run_values: List[Dict[str, float]],
        cumulative_names: Optional[List[str]] = None,
    ) -> List[TrendResult]:
        return self.analyze_all(
            {extractor_name: run_values},
            cumulative_names,
        )


def create_trend_analyzer() -> TrendAnalyzer:
    return TrendAnalyzer()
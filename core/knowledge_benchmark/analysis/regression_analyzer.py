"""
Regression Analyzer (RM-5.8.4)

Compares Current vs Baseline benchmark results across multiple metrics:
Precision, Recall, F1, Confidence, ECE, and Runtime.

Outputs PASS, WARNING, or FAIL status with delta and percentage drop.

Fully offline. Determinisci. No external dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import RegressionStatus, RegressionResult


_REGRESSION_METRICS = [
    "precision",
    "recall",
    "f1_score",
    "missing_rate",
    "hallucination_rate",
    "duplicate_rate",
    "schema_pass_rate",
    "business_rule_pass_rate",
    "ece",
]


_DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "f1_score": {"warning": 0.01, "fail": 0.02},
    "precision": {"warning": 0.01, "fail": 0.02},
    "recall": {"warning": 0.01, "fail": 0.02},
    "missing_rate": {"warning": 0.02, "fail": 0.05},
    "hallucination_rate": {"warning": 0.02, "fail": 0.05},
    "ece": {"warning": 0.02, "fail": 0.05},
    "schema_pass_rate": {"warning": 0.05, "fail": 0.10},
    "business_rule_pass_rate": {"warning": 0.05, "fail": 0.10},
    "duplicate_rate": {"warning": 0.02, "fail": 0.05},
}


_INVERTED_METRICS = {
    "missing_rate",
    "hallucination_rate",
    "duplicate_rate",
    "ece",
}


class RegressionAnalyzer:
    """Analyzes regression between current and baseline results for each extractor."""

    def __init__(
        self,
        thresholds: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        self.thresholds = thresholds or _DEFAULT_THRESHOLDS

    def analyze_all(
        self,
        current_scores: Dict[str, Dict[str, float]],
        baseline_scores: Optional[Dict[str, Dict[str, float]]],
    ) -> List[RegressionResult]:
        results: List[RegressionResult] = []

        if baseline_scores is None:
            return results

        for extractor_name, cur_metrics in current_scores.items():
            bl_metrics = baseline_scores.get(extractor_name)
            if bl_metrics is None:
                continue

            for metric_name in sorted(cur_metrics.keys()):
                if metric_name not in bl_metrics:
                    continue

                current_value = float(cur_metrics[metric_name])
                baseline_value = float(bl_metrics[metric_name])

                result = self._compute_regression(
                    extractor_name, metric_name, current_value, baseline_value
                )
                results.append(result)

        return results

    def _compute_regression(
        self,
        extractor_type: str,
        metric_name: str,
        current_value: float,
        baseline_value: float,
    ) -> RegressionResult:
        is_inverted = metric_name in _INVERTED_METRICS

        if is_inverted:
            delta = current_value - baseline_value
        else:
            delta = baseline_value - current_value

        if baseline_value != 0.0:
            delta_percent = (delta / abs(baseline_value)) * 100.0
        else:
            delta_percent = 0.0

        thresholds = self.thresholds.get(metric_name, {"warning": 0.02, "fail": 0.05})
        warning_threshold = thresholds["warning"]
        fail_threshold = thresholds["fail"]

        if delta < -0.0001:
            status = RegressionStatus.PASS
        elif delta < warning_threshold:
            status = RegressionStatus.PASS
        elif delta < fail_threshold:
            status = RegressionStatus.WARNING
        else:
            status = RegressionStatus.FAIL

        return RegressionResult(
            extractor_type=extractor_type,
            metric_name=metric_name,
            current_value=round(current_value, 4),
            baseline_value=round(baseline_value, 4),
            delta=round(delta, 4),
            delta_percent=round(delta_percent, 2),
            status=status,
        )

    def analyze_extractor_metrics(
        self,
        extractor_name: str,
        current_metrics: Dict[str, float],
        baseline_metrics: Optional[Dict[str, float]],
    ) -> List[RegressionResult]:
        results: List[RegressionResult] = []

        if baseline_metrics is None:
            return results

        for metric_name, current_value in current_metrics.items():
            if metric_name not in baseline_metrics:
                continue

            baseline_value = baseline_metrics[metric_name]
            result = self._compute_regression(
                extractor_name, metric_name,
                float(current_value), float(baseline_value),
            )
            results.append(result)

        return results

    def aggregate_regression_summary(
        self,
        results: List[RegressionResult],
    ) -> Dict[str, Any]:
        total = len(results)
        passes = sum(1 for r in results if r.status == RegressionStatus.PASS)
        warnings = sum(1 for r in results if r.status == RegressionStatus.WARNING)
        fails = sum(1 for r in results if r.status == RegressionStatus.FAIL)

        by_extractor: Dict[str, Dict[str, int]] = {}
        for r in results:
            if r.extractor_type not in by_extractor:
                by_extractor[r.extractor_type] = {"PASS": 0, "WARNING": 0, "FAIL": 0}
            by_extractor[r.extractor_type][r.status.value] += 1

        overall_status = "PASS"
        if fails > 0:
            overall_status = "FAIL"
        elif warnings > 0:
            overall_status = "WARNING"

        return {
            "total_comparisons": total,
            "passes": passes,
            "warnings": warnings,
            "fails": fails,
            "overall_status": overall_status,
            "by_extractor": by_extractor,
        }


def create_regression_analyzer() -> RegressionAnalyzer:
    return RegressionAnalyzer()
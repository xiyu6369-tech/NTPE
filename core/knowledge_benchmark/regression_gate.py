"""
Regression Gate (RM-5.8.5)

Formalized regression gate with per-metric thresholds.
Compares current benchmark results against active baseline
and produces a PASS/WARNING/FAIL decision for release qualification.

Thresholds:
    F1:        不得下降超過 1%
    Precision: 不得下降超過 2%
    Recall:    不得下降超過 2%
    Confidence (ECE): 不得下降超過 2%

Offline. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class GateStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class GateThreshold:
    metric_name: str
    warning_pct: float
    fail_pct: float
    is_inverted: bool = False


DEFAULT_GATE_THRESHOLDS: List[GateThreshold] = [
    GateThreshold("f1_score", 0.005, 0.01, is_inverted=False),
    GateThreshold("precision", 0.01, 0.02, is_inverted=False),
    GateThreshold("recall", 0.01, 0.02, is_inverted=False),
    GateThreshold("ece", 0.01, 0.02, is_inverted=True),
    GateThreshold("missing_rate", 0.01, 0.02, is_inverted=True),
    GateThreshold("hallucination_rate", 0.01, 0.02, is_inverted=True),
    GateThreshold("schema_pass_rate", 0.02, 0.05, is_inverted=False),
    GateThreshold("business_rule_pass_rate", 0.02, 0.05, is_inverted=False),
]


@dataclass
class MetricComparison:
    extractor_type: str
    metric_name: str
    current_value: float
    baseline_value: float
    delta: float
    delta_percent: float
    status: GateStatus
    threshold_warning: float
    threshold_fail: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 4),
            "baseline_value": round(self.baseline_value, 4),
            "delta": round(self.delta, 4),
            "delta_percent": round(self.delta_percent, 2),
            "status": self.status.value,
            "threshold_warning": self.threshold_warning,
            "threshold_fail": self.threshold_fail,
        }


@dataclass
class RegressionGateReport:
    overall_status: GateStatus = GateStatus.PASS
    comparisons: List[MetricComparison] = field(default_factory=list)
    failure_count: int = 0
    warning_count: int = 0
    pass_release: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "failure_count": self.failure_count,
            "warning_count": self.warning_count,
            "pass_release": self.pass_release,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class RegressionGate:
    """Formal regression gate with per-metric thresholds."""

    def __init__(
        self,
        thresholds: Optional[Dict[str, GateThreshold]] = None,
    ):
        self.thresholds = thresholds or {t.metric_name: t for t in DEFAULT_GATE_THRESHOLDS}

    def evaluate(
        self,
        current_scores: Dict[str, Dict[str, float]],
        baseline_scores: Dict[str, Dict[str, float]],
    ) -> RegressionGateReport:
        comparisons: List[MetricComparison] = []
        failures = 0
        warnings = 0

        for ext_name, cur_metrics in current_scores.items():
            bl_metrics = baseline_scores.get(ext_name)
            if bl_metrics is None:
                continue

            for metric_name, current_val in cur_metrics.items():
                baseline_val = bl_metrics.get(metric_name)
                if baseline_val is None:
                    continue

                threshold = self.thresholds.get(metric_name)
                if threshold is None:
                    continue

                if threshold.is_inverted:
                    delta = float(current_val) - float(baseline_val)
                else:
                    delta = float(baseline_val) - float(current_val)

                if abs(float(baseline_val)) > 0.0001:
                    delta_percent = (delta / abs(float(baseline_val))) * 100.0
                else:
                    delta_percent = 0.0

                if delta < -0.0001:
                    status = GateStatus.PASS
                elif delta <= threshold.warning_pct:
                    status = GateStatus.PASS
                elif delta <= threshold.fail_pct:
                    status = GateStatus.WARNING
                    warnings += 1
                else:
                    status = GateStatus.FAIL
                    failures += 1

                comparisons.append(MetricComparison(
                    extractor_type=ext_name,
                    metric_name=metric_name,
                    current_value=float(current_val),
                    baseline_value=float(baseline_val),
                    delta=round(delta, 4),
                    delta_percent=round(delta_percent, 2),
                    status=status,
                    threshold_warning=threshold.warning_pct,
                    threshold_fail=threshold.fail_pct,
                ))

        overall = GateStatus.PASS
        if failures > 0:
            overall = GateStatus.FAIL
        elif warnings > 0:
            overall = GateStatus.WARNING

        return RegressionGateReport(
            overall_status=overall,
            comparisons=comparisons,
            failure_count=failures,
            warning_count=warnings,
            pass_release=(overall != GateStatus.FAIL),
        )


def create_regression_gate() -> RegressionGate:
    return RegressionGate()
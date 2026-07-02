from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping


@dataclass
class RegressionFinding:
    metric: str
    baseline: float
    current: float
    delta: float
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "baseline": self.baseline,
            "current": self.current,
            "delta": self.delta,
            "status": self.status,
        }


class RegressionAnalyzer:
    def __init__(self, threshold: float = 0.10):
        self.threshold = max(0.0, float(threshold))

    def compare(self, baseline: Mapping[str, Any], current: Mapping[str, Any], metrics: Iterable[str] | None = None) -> Dict[str, Any]:
        metrics = list(metrics or ["elapsed_ms", "peak_memory_bytes"])
        findings: List[RegressionFinding] = []
        base_summary = baseline.get("summary", {}) if isinstance(baseline, Mapping) else {}
        cur_summary = current.get("summary", {}) if isinstance(current, Mapping) else {}
        for metric in metrics:
            b = float(base_summary.get(metric, 0.0) or 0.0)
            c = float(cur_summary.get(metric, 0.0) or 0.0)
            if b == 0:
                delta = 0.0 if c == 0 else 1.0
            else:
                delta = (c - b) / b
            if delta > self.threshold:
                status = "REGRESSION"
            elif delta < -self.threshold:
                status = "IMPROVEMENT"
            else:
                status = "STABLE"
            findings.append(RegressionFinding(metric, b, c, delta, status))
        return {
            "schema": "ntpe.performance.regression.v1",
            "threshold": self.threshold,
            "status": "REGRESSION" if any(f.status == "REGRESSION" for f in findings) else "PASS",
            "findings": [f.to_dict() for f in findings],
        }


def build_regression_report(baseline: Mapping[str, Any], current: Mapping[str, Any], threshold: float = 0.10) -> Dict[str, Any]:
    return RegressionAnalyzer(threshold=threshold).compare(baseline, current)

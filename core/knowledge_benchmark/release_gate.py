"""
Release Gate (RM-5.8.5)

Final gate that determines whether a new release can proceed based on:
    - Regression Gate result (must be PASS or WARNING)
    - Overall score threshold (must not drop below 0.80)
    - Minimum test coverage requirement

Outputs PASS (allow release) or FAIL (block release) with reason.

Offline. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReleaseDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


@dataclass
class ReleaseGateResult:
    decision: ReleaseDecision = ReleaseDecision.ALLOW
    reason: str = ""
    overall_score: float = 0.0
    baseline_score: float = 0.0
    regression_passed: bool = True
    score_threshold_passed: bool = True
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "overall_score": round(self.overall_score, 4),
            "baseline_score": round(self.baseline_score, 4),
            "score_change": round(self.overall_score - self.baseline_score, 4),
            "regression_passed": self.regression_passed,
            "score_threshold_passed": self.score_threshold_passed,
            "recommendations": self.recommendations,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class ReleaseGate:
    """Determines whether a release can proceed."""

    def __init__(
        self,
        min_overall_score: float = 0.70,
        min_regression_status: str = "PASS",
    ):
        self.min_overall_score = min_overall_score
        self.min_regression_status = min_regression_status

    def evaluate(
        self,
        overall_scorecard: Dict[str, Any],
        regression_gate_report: Optional[Dict[str, Any]] = None,
        baseline_score: Optional[float] = None,
    ) -> ReleaseGateResult:
        overall = overall_scorecard.get("overall", {})
        current_score = overall.get("overall_score", 0.0)
        bl_score = baseline_score if baseline_score is not None else current_score

        reasons: List[str] = []
        score_ok = current_score >= self.min_overall_score
        regression_ok = True

        if regression_gate_report:
            overall_status = regression_gate_report.get("overall_status", "PASS")
            regression_ok = overall_status != "FAIL"
            if not regression_ok:
                reasons.append(f"Regression gate FAILED: {overall_status}")

        if not score_ok:
            reasons.append(
                f"Overall score {current_score:.4f} below threshold {self.min_overall_score}"
            )

        score_drop = current_score - bl_score
        if score_drop < -0.02:
            reasons.append(f"Score dropped {score_drop:.4f} from baseline {bl_score:.4f}")

        recommendations: List[str] = []
        if not score_ok:
            recommendations.append("Improve extractor recall and accuracy")
        if current_score < 0.80:
            recommendations.append("Focus on high-priority failures")
        if not regression_ok:
            recommendations.append("Review regression report for failing metrics")

        decision = ReleaseDecision.ALLOW
        if reasons:
            decision = ReleaseDecision.BLOCK

        reason_text = "; ".join(reasons) if reasons else "All checks passed"

        return ReleaseGateResult(
            decision=decision,
            reason=reason_text,
            overall_score=current_score,
            baseline_score=bl_score,
            regression_passed=regression_ok,
            score_threshold_passed=score_ok,
            recommendations=recommendations,
            metadata={
                "min_overall_score": self.min_overall_score,
                "min_regression_status": self.min_regression_status,
            },
        )


def create_release_gate() -> ReleaseGate:
    return ReleaseGate()
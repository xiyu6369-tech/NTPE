from __future__ import annotations

from dataclasses import dataclass, field

from .model import RollbackDecision

ROLLBACK_VERSION = "7.0.0-stage08.4"


@dataclass
class RollbackController:
    disabled: bool = False
    reasons: list[str] = field(default_factory=list)

    def trigger(self, *reasons: str) -> RollbackDecision:
        self.disabled = True
        self.reasons.extend(reason for reason in reasons if reason and reason not in self.reasons)
        return RollbackDecision(ROLLBACK_VERSION, True, "disabled", tuple(self.reasons))


def evaluate_automatic_rollback(
    *,
    new_issues: tuple[str, ...] = (),
    quality_score: int | None = None,
    baseline_quality_score: int | None = None,
    qa_failure_rate: float | None = None,
    baseline_qa_failure_rate: float | None = None,
    provider_calls_added: int = 0,
    anchor_mismatch: bool = False,
    replacement_count: int = 1,
    metrics_complete: bool = True,
    evidence_match: bool = True,
    kill_switch: bool = False,
    artifact_integrity: bool = True,
    provider_status: str = "success",
) -> RollbackDecision:
    reasons: list[str] = []
    normalized = tuple(str(issue).upper() for issue in new_issues)
    if any("OMISSION" in issue for issue in normalized):
        reasons.append("new-omission-issue")
    if any("UNSUPPORTED" in issue or "ADDED_DETAIL" in issue for issue in normalized):
        reasons.append("new-unsupported-detail-issue")
    if quality_score is not None and baseline_quality_score is not None and quality_score < baseline_quality_score:
        reasons.append("quality-score-regression")
    if qa_failure_rate is not None and baseline_qa_failure_rate is not None and qa_failure_rate > baseline_qa_failure_rate:
        reasons.append("qa-failure-rate-regression")
    if provider_calls_added != 0:
        reasons.append("provider-calls-added")
    if anchor_mismatch:
        reasons.append("payload-anchor-mismatch")
    if replacement_count != 1:
        reasons.append("unexpected-context-replacement-count")
    if not metrics_complete:
        reasons.append("metrics-missing")
    if not evidence_match:
        reasons.append("evidence-mismatch")
    if kill_switch:
        reasons.append("kill-switch-enabled")
    if not artifact_integrity:
        reasons.append("production-artifact-integrity-failure")
    provider_limitation = provider_status if provider_status in {"timeout", "503"} else ""
    return RollbackDecision(ROLLBACK_VERSION, bool(reasons), "disabled" if reasons else "production_canary", tuple(dict.fromkeys(reasons)), provider_limitation)

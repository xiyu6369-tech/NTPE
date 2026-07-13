from __future__ import annotations

from typing import Any

from .model import BenchmarkRun


def evaluate_readiness(baseline: BenchmarkRun, candidate: BenchmarkRun, performance: dict[str, Any], quality: dict[str, Any], blockers: tuple[str, ...]) -> tuple[str, bool, tuple[str, ...], tuple[str, ...]]:
    reasons = list(blockers); limitations: list[str] = []
    external = any(row.timeout_count or row.http_503_count for row in (*baseline.chunks, *candidate.chunks))
    if external:
        limitations.append("external-provider-condition")
        return "incomplete_external_provider_limitation", False, tuple(dict.fromkeys(reasons)), tuple(limitations)
    if performance.get("activated_chunks", 0) < 1: reasons.append("no-activated-paired-chunk")
    if performance.get("provider_calls_added", 0) > 0: reasons.append("provider-calls-added")
    if quality.get("candidate_accepted_rate", 0) < quality.get("baseline_accepted_rate", 0): reasons.append("accepted-rate-regression")
    if quality.get("candidate_quality_score", 0) < quality.get("baseline_quality_score", 0): reasons.append("quality-score-regression")
    if quality.get("candidate_completeness_issues", 0) > quality.get("baseline_completeness_issues", 0): reasons.append("completeness-regression")
    if candidate.rollback_triggered: reasons.append("rollback-triggered")
    if not quality.get("quality_evidence_complete", False): reasons.append("quality-evidence-incomplete")
    if not baseline.artifact_integrity or not candidate.artifact_integrity: reasons.append("artifact-integrity-failure")
    if candidate.contract.rollout_percent > 5: reasons.append("production-rollout-exceeds-five-percent")
    if baseline.mode == "provider" and (not baseline.provider_evidence_complete or not candidate.provider_evidence_complete): reasons.append("provider-timing-evidence-incomplete")
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return "blocked", False, tuple(reasons), tuple(limitations)
    if not performance.get("performance_gain", False):
        return "pass_without_performance_gain", False, (), tuple(limitations)
    return "pass", True, (), tuple(limitations)

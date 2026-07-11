from __future__ import annotations

from pathlib import Path

from core.translation_discipline import (
    ACCEPT_WITH_WARNINGS,
    PROVIDER_RETRY,
    AdaptiveRetryDecisionEngine,
    apply_adaptive_retry_decision,
)


def _issue(code: str, route: str, severity: str = "medium", retry: bool = False) -> dict:
    return {
        "code": code,
        "severity": severity,
        "retry_required": retry,
        "metadata": {"discipline_route": route},
    }


def test_stage05_centralizes_runtime_retry_routing() -> None:
    engine = AdaptiveRetryDecisionEngine()
    local_report = {
        "decision": "retry_required",
        "retry_required": True,
        "merged_issues": [_issue("NATURALNESS_GUARD", "local_repair")],
    }
    provider_report = {
        "decision": "retry_required",
        "retry_required": True,
        "merged_issues": [_issue("HANGUL_RESIDUE", "provider_retry", "high", True)],
    }

    assert engine.decide(local_report, post_repair=True).action == ACCEPT_WITH_WARNINGS
    assert engine.decide(provider_report, post_repair=True).action == PROVIDER_RETRY

    runtime = {
        "passed": False,
        "status": "retry_required",
        "decision": "retry_required",
        "retry_required": True,
        "issues": [],
        "unified_quality_report": local_report,
    }
    result = apply_adaptive_retry_decision(runtime, post_repair=True)
    assert result["passed"] is True
    assert result["adaptive_retry_decision"]["version"] == "6.0.0-stage05"
    assert result["smart_local_repair"]["provider_retry_skipped"] is True

    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "apply_adaptive_retry_decision" in runtime_source
    assert "adaptive-retry-decision" in runtime_source
    assert "apply_smart_local_repair_decision(" not in runtime_source

from __future__ import annotations

from core.translation_discipline import (
    ACCEPT,
    ACCEPT_WITH_WARNINGS,
    LOCAL_REPAIR,
    PROVIDER_RETRY,
    REJECT,
    AdaptiveRetryDecisionEngine,
    LocalRepairResult,
    apply_adaptive_retry_decision,
)


def issue(code: str, route: str, severity: str = "medium", retry: bool = False) -> dict:
    return {
        "code": code,
        "severity": severity,
        "retry_required": retry,
        "metadata": {"discipline_route": route},
    }


def report(*issues: dict, decision: str = "retry_required") -> dict:
    return {
        "decision": decision,
        "accepted": decision.startswith("accepted"),
        "passed": decision.startswith("accepted"),
        "retry_required": decision == "retry_required",
        "merged_issues": list(issues),
    }


def main() -> int:
    engine = AdaptiveRetryDecisionEngine()

    clean = engine.decide(report(decision="accepted"))
    assert clean.action == ACCEPT

    local = engine.decide(report(issue("SIMPLIFIED_CHINESE", "local_repair")), post_repair=False)
    assert local.action == LOCAL_REPAIR

    repaired = LocalRepairResult(
        text="一週",
        changed=True,
        attempted_codes=("SIMPLIFIED_CHINESE",),
        repaired_codes=("SIMPLIFIED_CHINESE",),
    )
    local_done = engine.decide(
        report(issue("SIMPLIFIED_CHINESE", "local_repair")),
        local_repair_result=repaired,
        post_repair=True,
    )
    assert local_done.action == ACCEPT_WITH_WARNINGS

    provider = engine.decide(report(issue("PARAGRAPH_OMISSION_SUSPECTED", "provider_retry", "high", True)))
    assert provider.action == PROVIDER_RETRY

    critical = engine.decide(report(issue("UNKNOWN_CRITICAL", "warning", "critical", False)))
    assert critical.action == REJECT

    runtime = {
        "passed": False,
        "status": "retry_required",
        "decision": "retry_required",
        "retry_required": True,
        "issues": [],
        "unified_quality_report": report(issue("NATURALNESS_GUARD", "local_repair")),
    }
    applied = apply_adaptive_retry_decision(runtime, post_repair=True)
    assert applied["passed"] is True
    assert applied["decision"] == "accepted_with_warnings"
    assert applied["smart_local_repair"]["provider_retry_skipped"] is True

    print("NTPE TE v6.0 Stage 05 Adaptive Retry Decision Engine")
    print("====================================================")
    print("Clean result accepted                    PASS")
    print("Local issue routes to repair             PASS")
    print("Post-repair local warning accepted       PASS")
    print("Completeness issue routes to provider    PASS")
    print("Unrouted critical issue rejected         PASS")
    print("v5 smart-local compatibility preserved   PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

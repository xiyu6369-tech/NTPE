from __future__ import annotations

from core.translation_quality_v5.smart_local_repair import apply_smart_local_repair_decision
from core.translation_quality_v5.unified_quality_gate import run_unified_quality_gate


def _v5_issue(code: str, severity: str, retry: bool = True) -> dict:
    return {
        "accepted": not retry,
        "retry_required": retry,
        "issues": [{
            "code": code,
            "type": code,
            "severity": severity,
            "message": code,
            "retry_required": retry,
        }],
    }


def main() -> int:
    local = run_unified_quality_gate(_v5_issue("SIMPLIFIED_CHINESE", "medium"), {"passed": True, "issues": []})
    assert local["decision"] == "retry_required"
    assert local["score"] == 90
    issue = local["merged_issues"][0]
    assert issue["metadata"]["discipline_route"] == "local_repair"
    assert local["discipline_quality_enforcement"]["decision_preserved"] is True

    routed = apply_smart_local_repair_decision({
        "decision": local["decision"],
        "status": local["decision"],
        "passed": False,
        "retry_required": True,
        "issues": [],
        "unified_quality_report": local,
    })
    assert routed["decision"] == "accepted_with_warnings"
    assert routed["smart_local_repair"]["provider_retry_skipped"] is True

    blocking = run_unified_quality_gate(_v5_issue("PARAGRAPH_OMISSION_SUSPECTED", "high"), {"passed": True, "issues": []})
    assert blocking["decision"] == "retry_required"
    assert blocking["merged_issues"][0]["metadata"]["discipline_route"] == "provider_retry"
    assert blocking["merged_issues"][0]["metadata"]["discipline_rule_code"] == "PRESERVE_PARAGRAPH_INTENT"

    clean = run_unified_quality_gate({"accepted": True, "retry_required": False, "issues": []}, {"passed": True, "issues": []})
    assert clean["decision"] == "accepted"
    assert clean["score"] == 100
    assert clean["discipline_quality_enforcement"]["route_counts"] == {
        "local_repair": 0, "provider_retry": 0, "warning": 0,
    }

    print("TE v6.0 Stage 03 Discipline Quality Enforcement")
    print("================================================")
    print("Quality score/decision preserved      PASS")
    print("Local issues route to local repair    PASS")
    print("Blocking issues route to provider     PASS")
    print("Discipline rule mapping attached      PASS")
    print("Clean output remains accepted         PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

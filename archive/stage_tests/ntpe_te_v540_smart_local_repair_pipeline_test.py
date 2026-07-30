from core.translation_quality_v5.smart_local_repair import apply_smart_local_repair_decision


def report(code: str, severity: str = "high") -> dict:
    issue = {"code": code, "severity": severity, "retry_required": True, "message": code}
    return {
        "passed": False,
        "decision": "retry_required",
        "retry_required": True,
        "issues": [dict(issue)],
        "unified_quality_report": {
            "decision": "retry_required",
            "passed": False,
            "accepted": False,
            "retry_required": True,
            "merged_issues": [dict(issue)],
        },
    }


def main() -> int:
    natural = apply_smart_local_repair_decision(report("NATURALNESS_GUARD"))
    assert natural["decision"] == "accepted_with_warnings"
    assert natural["passed"] is True
    assert natural["smart_local_repair"]["provider_retry_skipped"] is True

    simplified = apply_smart_local_repair_decision(report("SIMPLIFIED_CHINESE"), local_repairs=[{"from": "一周", "to": "一週"}])
    assert simplified["decision"] == "accepted_with_warnings"

    omitted = apply_smart_local_repair_decision(report("PARAGRAPH_OMISSION_SUSPECTED"))
    assert omitted["decision"] == "retry_required"
    assert omitted["passed"] is False

    repeated = apply_smart_local_repair_decision(report("SEMANTIC_DUPLICATE_PARAGRAPH"))
    assert repeated["decision"] == "retry_required"

    print("TE v5.4.0 Smart Local Repair Pipeline Test")
    print("==========================================")
    print("Naturalness-only retry skipped       PASS")
    print("Deterministic repair retry skipped   PASS")
    print("Omission remains provider-blocking   PASS")
    print("Semantic repetition remains blocking PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

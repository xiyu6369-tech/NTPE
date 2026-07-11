from core.translation_quality_v5.unified_quality_gate import run_unified_quality_gate


def main() -> int:
    report = {
        "accepted": False,
        "retry_required": True,
        "issues": [
            {
                "code": "SIMPLIFIED_CHINESE",
                "severity": "medium",
                "message": "policy=normalize",
                "repair_action": "full_traditional_chinese_conversion",
            },
            {
                "code": "PARAGRAPH_STRUCTURE_MERGED",
                "severity": "medium",
                "message": "natural paragraph merge",
            },
        ],
    }
    result = run_unified_quality_gate(report, {"passed": True, "issues": []})
    assert result["decision"] == "accepted_with_warnings", result
    assert result["score"] == 80, result
    assert not result["retry_required"], result
    assert all(not issue["retry_required"] for issue in result["merged_issues"]), result

    blocking = run_unified_quality_gate({
        "accepted": False,
        "retry_required": True,
        "issues": [{
            "code": "TOO_SHORT",
            "severity": "high",
            "message": "missing content",
        }],
    }, {"passed": True, "issues": []})
    assert blocking["decision"] == "retry_required", blocking

    print("TE v5.3.1.2 Unified Nonblocking Issue Mapping")
    print("================================================")
    print("Aggregate retry not copied to warnings  PASS")
    print("Normalize issue remains nonblocking     PASS")
    print("Paragraph merge remains nonblocking     PASS")
    print("True high issue remains blocking        PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

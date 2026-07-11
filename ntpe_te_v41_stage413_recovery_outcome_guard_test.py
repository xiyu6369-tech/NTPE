
from core.translation_reliability import RecoveryOutcomeGuard


def check(name, condition):
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.3 Recovery Outcome Guard Test")
    print("=" * 78)

    guard = RecoveryOutcomeGuard()

    recovery_success = {
        "success": True,
        "status": "completed",
        "final_outcome": "success",
        "attempts_used": 2,
        "split_count": 1,
        "rebuild_count": 0,
    }

    accepted = guard.evaluate(
        "가" * 100,
        "譯" * 90,
        recovery_success,
    )
    check("Valid Output Accepted", accepted["accepted"] is True)
    check("Accepted Has No Issues", accepted["issues"] == [])
    check("Accepted Result Valid", guard.validate_result(accepted))

    empty = guard.evaluate(
        "가" * 100,
        "",
        recovery_success,
    )
    check("Empty Output Rejected", empty["accepted"] is False)
    check("Empty Issue Present", "empty_output" in empty["issues"])

    short = guard.evaluate(
        "가" * 100,
        "短" * 10,
        recovery_success,
    )
    check("Short Output Rejected", short["accepted"] is False)
    check("Short Issue Present", "too_short" in short["issues"])

    hangul = guard.evaluate(
        "가" * 100,
        "這是譯文가",
        recovery_success,
    )
    check("Hangul Rejected", hangul["accepted"] is False)
    check("Hangul Issue Present", "hangul_residue" in hangul["issues"])

    duplicate = guard.evaluate(
        "가" * 100,
        "第一段\n第二段\n第二段\n第三段",
        recovery_success,
        {"min_length_ratio": 0.01},
    )
    check("Duplicate Rejected", duplicate["accepted"] is False)
    check("Duplicate Issue Present", "duplicate_output" in duplicate["issues"])

    recovery_failed = guard.evaluate(
        "가" * 100,
        "譯" * 90,
        {
            "success": False,
            "status": "failed",
            "final_outcome": "read_timeout",
        },
    )
    check("Failed Recovery Rejected", recovery_failed["accepted"] is False)
    check("Recovery Failure Issue", "recovery_not_successful" in recovery_failed["issues"])

    for result in [empty, short, hangul, duplicate, recovery_failed]:
        check("Rejected Result Valid", guard.validate_result(result))

    check("No Source Retention", accepted["source_text_retained"] is False)
    check("No Translation Retention", accepted["translated_text_retained"] is False)
    check("No Provider Call", accepted["integration_status"]["provider_called"] is False)
    check("No HTTP Call", accepted["integration_status"]["http_called"] is False)
    check("No API Key Access", accepted["integration_status"]["api_key_accessed"] is False)
    check("No Runtime Modification", accepted["integration_status"]["runtime_modified"] is False)
    check("No Real Translation", accepted["integration_status"]["real_translation_executed"] is False)

    print("NTPE TE-v4.1 Stage-4.1.3 Recovery Outcome Guard PASS")


if __name__ == "__main__":
    main()

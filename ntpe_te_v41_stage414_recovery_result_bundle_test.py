
from core.translation_reliability import RecoveryResultBundle


def check(name, condition):
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.4 Recovery Result Bundle Test")
    print("=" * 76)

    builder = RecoveryResultBundle()

    hook_success = {
        "status": "recovery_completed",
        "allowed": True,
        "blocked": False,
        "runtime_id": "demo-414",
        "recovery_summary": {
            "success": True,
            "attempts_used": 2,
            "rebuild_count": 0,
            "split_count": 1,
            "final_outcome": "success",
        },
    }
    guard_accept = {
        "accepted": True,
        "status": "accepted",
        "issues": [],
        "metrics": {
            "source_chars": 100,
            "translated_chars": 90,
            "length_ratio": 0.9,
            "hangul_residue_count": 0,
            "duplicate_line_count": 0,
        },
    }

    accepted = builder.build(
        "demo-414",
        hook_success,
        guard_accept,
        {
            "profile": "literary",
            "source_text": "must-not-retain",
            "api_key": "must-not-retain",
        },
    )

    check("Accepted Bundle", accepted["accepted"] is True)
    check("Accepted Status", accepted["status"] == "recovery_accepted")
    check("Runtime ID Preserved", accepted["runtime_id"] == "demo-414")
    check("Attempts Preserved", accepted["recovery_summary"]["attempts_used"] == 2)
    check("Guard Issues Empty", accepted["guard_summary"]["issues"] == [])
    check("Bundle Valid", builder.validate_bundle(accepted))
    check("Blocked Metadata Removed", "source_text" not in accepted["metadata"])
    check("API Key Removed", "api_key" not in accepted["metadata"])

    guard_reject = {
        "accepted": False,
        "status": "rejected",
        "issues": ["too_short"],
        "metrics": {
            "source_chars": 100,
            "translated_chars": 10,
            "length_ratio": 0.1,
            "hangul_residue_count": 0,
            "duplicate_line_count": 0,
        },
    }

    rejected = builder.build(
        "demo-414",
        hook_success,
        guard_reject,
    )
    check("Rejected Bundle", rejected["accepted"] is False)
    check("Rejected Status", rejected["status"] == "recovery_rejected")
    check("Rejected Issue Preserved", rejected["guard_summary"]["issues"] == ["too_short"])
    check("Rejected Bundle Valid", builder.validate_bundle(rejected))

    hook_failed = {
        "status": "recovery_failed",
        "allowed": True,
        "blocked": False,
        "runtime_id": "demo-414",
        "recovery_summary": {
            "success": False,
            "attempts_used": 3,
            "rebuild_count": 1,
            "split_count": 1,
            "final_outcome": "read_timeout",
        },
    }

    failed = builder.build("demo-414", hook_failed, guard_accept)
    check("Failed Hook Rejected", failed["accepted"] is False)
    check("Failed Outcome Preserved", failed["final_outcome"] == "read_timeout")
    check("Failed Bundle Valid", builder.validate_bundle(failed))

    check("No Source Retention", accepted["source_text_retained"] is False)
    check("No Translation Retention", accepted["translated_text_retained"] is False)
    check("No Runtime Modification", accepted["integration_status"]["runtime_modified"] is False)
    check("No Provider Modification", accepted["integration_status"]["provider_runtime_modified"] is False)
    check("No HTTP Call", accepted["integration_status"]["http_called"] is False)
    check("No API Key Access", accepted["integration_status"]["api_key_accessed"] is False)
    check("No Real Runtime", accepted["integration_status"]["real_translation_runtime_used"] is False)

    print("NTPE TE-v4.1 Stage-4.1.4 Recovery Result Bundle PASS")


if __name__ == "__main__":
    main()

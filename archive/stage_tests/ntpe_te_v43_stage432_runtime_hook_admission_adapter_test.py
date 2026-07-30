from core.translation_reliability import (
    RuntimeHookAdmissionAdapter,
    TranslationRuntimeRecoveryHookContract,
)


def check(name, condition):
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def safe_request():
    return {
        "caller": "translation_runtime",
        "runtime_id": "runtime-432",
        "session_id": "session-432",
        "job_id": "job-432",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "failure_outcome": "read_timeout",
        "retry_count": 1,
        "provider_attempts": 1,
        "latency_ms": 180000,
        "runtime_status": "failed",
        "hook_mode": "shadow_only",
    }


def readiness():
    return {
        "approved": True,
        "status": "ready",
        "te_v40_freeze": True,
        "te_v41_freeze": True,
        "te_v42_freeze": True,
    }


def main():
    print("NTPE TE-v4.3 Stage-4.3.2 Runtime Hook Admission Adapter Test")
    print("=" * 88)
    contract = TranslationRuntimeRecoveryHookContract().build_contract()
    adapter = RuntimeHookAdmissionAdapter()

    rejected = adapter.evaluate_hook_request(safe_request(), contract, readiness(), {"enabled": False, "mode": "runtime_shadow_hook"})
    check("Flag Disabled Rejected", rejected["admitted"] is False)
    check("Rejected Valid", adapter.validate_result(rejected))

    wrong = safe_request()
    wrong["caller"] = "tool"
    wrong_result = adapter.evaluate_hook_request(wrong, contract, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Wrong Caller Rejected", "invalid_caller" in wrong_result["failed_checks"])

    forbidden = safe_request()
    forbidden["metadata"] = {"nested": [{"source_text": "raw"}, {"api_key": "secret"}]}
    forbidden_result = adapter.evaluate_hook_request(forbidden, contract, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Forbidden Rejected", "forbidden_input_present" in forbidden_result["failed_checks"])
    check("Raw Not Retained", "raw" not in str(forbidden_result))
    check("Secret Not Retained", "secret" not in str(forbidden_result))

    admitted = adapter.evaluate_hook_request(safe_request(), contract, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Admitted", admitted["status"] == "admitted_for_runtime_shadow_hook")
    check("Execution Disabled", admitted["execution_allowed"] is False)
    check("No Replacement", admitted["result_replacement_allowed"] is False)
    check("No Fallback", admitted["provider_fallback_allowed"] is False)
    check("Rollback Available", admitted["rollback_available"] is True)
    check("is_admitted", adapter.is_admitted(admitted))
    check("Admitted Valid", adapter.validate_result(admitted))
    print("NTPE TE-v4.3 Stage-4.3.2 Runtime Hook Admission Adapter PASS")


if __name__ == "__main__":
    main()

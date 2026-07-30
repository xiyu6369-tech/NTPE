from core.translation_reliability import (
    RuntimeHookAdmissionAdapter,
    RuntimeSingleChunkShadowHook,
    TranslationRuntimeRecoveryHookContract,
)


def check(name, condition):
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def request():
    return {
        "caller": "translation_runtime",
        "runtime_id": "runtime-433",
        "session_id": "session-433",
        "job_id": "job-433",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "failure_outcome": "read_timeout",
        "retry_count": 1,
        "provider_attempts": 1,
        "latency_ms": 180000,
        "hook_mode": "shadow_only",
    }


def admission(req):
    contract = TranslationRuntimeRecoveryHookContract().build_contract()
    readiness = {"approved": True, "status": "ready", "te_v40_freeze": True, "te_v41_freeze": True, "te_v42_freeze": True}
    return RuntimeHookAdmissionAdapter().evaluate_hook_request(req, contract, readiness, {"enabled": True, "mode": "runtime_shadow_hook"})


def main():
    print("NTPE TE-v4.3 Stage-4.3.3 Runtime Single Chunk Shadow Hook Test")
    print("=" * 88)
    hook = RuntimeSingleChunkShadowHook()
    req = request()
    adm = admission(req)

    blocked = hook.invoke(req, {"admitted": False, "status": "rejected"}, lambda payload: {})
    check("Rejected Admission Blocks", blocked["status"] == "shadow_hook_blocked")
    check("Blocked Callback Not Called", blocked["callback_called"] is False)

    no_callback = hook.invoke(req, adm, None)
    check("Missing Callback Blocks", no_callback["status"] == "shadow_hook_blocked")

    seen = {}

    def callback(payload):
        seen.update(payload)
        return {"runtime_status": "observed", "recovery_recommended": True, "recommended_action": "split_and_retry", "mock": True}

    completed = hook.invoke(req, adm, callback)
    check("Completed", completed["status"] == "shadow_hook_completed")
    check("Callback Called", completed["callback_called"] is True)
    check("Callback Metadata Only", "source_text" not in seen and "text" not in seen)
    check("No Result Replacement", completed["result_replaced"] is False)
    check("No Provider Fallback", completed["provider_fallback_executed"] is False)
    check("No Provider Request", completed["real_provider_request_executed"] is False)
    check("Completed Valid", hook.validate_result(completed))
    check("is_completed", hook.is_completed(completed))

    failed = hook.invoke(req, adm, lambda payload: "bad")
    check("Non Mapping Fails", failed["status"] == "shadow_hook_failed")
    check("Failed Valid", hook.validate_result(failed))

    def raises(payload):
        raise RuntimeError("boom")

    exception_result = hook.invoke(req, adm, raises)
    check("Exception Contained", exception_result["status"] == "shadow_hook_failed")
    check("Exception Valid", hook.validate_result(exception_result))
    print("NTPE TE-v4.3 Stage-4.3.3 Runtime Single Chunk Shadow Hook PASS")


if __name__ == "__main__":
    main()

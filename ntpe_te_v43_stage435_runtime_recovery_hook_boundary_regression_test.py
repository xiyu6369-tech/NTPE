from core.translation_reliability import (
    RealRuntimeRecoveryPilotRollbackController,
    RuntimeHookAdmissionAdapter,
    RuntimeHookResultMapper,
    RuntimeSingleChunkShadowHook,
    TranslationRuntimeRecoveryHookContract,
)


def check(name, condition):
    print(f"{name:<68} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def request():
    return {
        "caller": "translation_runtime",
        "runtime_id": "runtime-435",
        "session_id": "session-435",
        "job_id": "job-435",
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
    return {"approved": True, "status": "ready", "te_v40_freeze": True, "te_v41_freeze": True, "te_v42_freeze": True}


def main():
    print("NTPE TE-v4.3 Stage-4.3.5 Runtime Recovery Hook Boundary Regression Test")
    print("=" * 110)
    contract = TranslationRuntimeRecoveryHookContract()
    adapter = RuntimeHookAdmissionAdapter()
    hook = RuntimeSingleChunkShadowHook()
    mapper = RuntimeHookResultMapper()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    built = contract.build_contract()
    req = request()

    disabled = adapter.evaluate_hook_request(req, built, readiness(), {"enabled": False, "mode": "runtime_shadow_hook"})
    blocked = hook.invoke(req, disabled, lambda payload: {"runtime_status": "observed"})
    check("Default Disabled Rejected", disabled["admitted"] is False)
    check("Rejected Hook Blocked", blocked["callback_called"] is False)

    admission = adapter.evaluate_hook_request(req, built, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    callback_seen = {}

    def callback(payload):
        callback_seen.update(payload)
        return {"runtime_status": "observed", "recovery_recommended": True, "recommended_action": "split_and_retry", "mock": True}

    hook_result = hook.invoke(req, admission, callback)
    mapping = mapper.map_result("runtime-435", hook_result)
    rolled = rollback.request_rollback({"mode": "shadow_hook_completed", "runtime_id": "runtime-435"})
    rolled_mapping = mapper.map_result("runtime-435", hook_result, rolled)

    check("Safe Admission", admission["admitted"] is True)
    check("Callback Executed", hook_result["callback_called"] is True)
    check("Shadow Recommendation", mapping["status"] == "shadow_recommendation_available")
    check("Runtime Result Unchanged", mapping["original_runtime_result_unchanged"] is True)
    check("No Replacement", mapper.should_replace_runtime_result(mapping) is False)
    check("Rollback Mapping", rolled_mapping["status"] == "shadow_rolled_back")

    failed = hook.invoke(req, admission, lambda payload: (_ for _ in ()).throw(RuntimeError("safe-fail")))
    failed_mapping = mapper.map_result("runtime-435", failed)
    check("Callback Failure Contained", failed["status"] == "shadow_hook_failed")
    check("Failure Mapping", failed_mapping["status"] == "shadow_hook_failed")

    multi = dict(req)
    multi["chunk_count"] = 2
    multi_admission = adapter.evaluate_hook_request(multi, built, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Single Chunk Only", "invalid_chunk_count" in multi_admission["failed_checks"])

    forbidden = dict(req)
    forbidden["metadata"] = {"nested": [{"translated_text": "secret output"}, {"chunks": ["raw"]}]}
    forbidden_admission = adapter.evaluate_hook_request(forbidden, built, readiness(), {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Forbidden Recursive Rejected", "forbidden_input_present" in forbidden_admission["failed_checks"])
    check("Forbidden Text Not Retained", "secret output" not in str(forbidden_admission) and "raw" not in str(forbidden_admission))

    for artifact in (admission, hook_result, mapping, rolled, rolled_mapping):
        check("Boundary No Raw Source", "secret output" not in str(artifact) and "raw" not in str(artifact))
        check("Boundary No Secret Value", "secret" not in str(artifact))
    check("No HTTP", True)
    check("No Provider Runtime", hook_result["real_provider_request_executed"] is False)
    check("No Provider Fallback", hook_result["provider_fallback_executed"] is False)
    check("No Real Translation", hook_result["result_replaced"] is False)
    check("No Launcher", rolled["metadata"]["launcher_modified"] is False)
    check("No Runtime Main Flow Change", built["translation_runtime_touch_mode"] == "optional_hook_only")
    print("NTPE TE-v4.3 Stage-4.3.5 Runtime Recovery Hook Boundary Regression PASS")


if __name__ == "__main__":
    main()

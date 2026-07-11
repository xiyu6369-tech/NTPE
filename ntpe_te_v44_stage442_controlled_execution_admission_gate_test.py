from core.translation_reliability import ControlledExecutionAdmissionGate, ControlledExecutionContract


def check(name, condition):
    print(f"{name:<64} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def safe_request():
    return {
        "caller": "translation_runtime", "execution_mode": "single_chunk_controlled_recovery",
        "runtime_id": "runtime-442", "chunk_index": 1, "chunk_count": 1,
        "recovery_execution_count": 1, "original_result_id": "original-442",
        "recovery_candidate_id": "candidate-442", "failure_outcome": "read_timeout",
    }


def readiness():
    return {
        "approved": True, "status": "ready_for_controlled_execution", "te_v40_freeze": True,
        "te_v41_freeze": True, "te_v42_freeze": True, "te_v43_freeze": True,
        "real_provider_request_allowed": False, "provider_fallback_allowed": False,
        "real_translation_allowed": False,
    }


def shadow():
    return {
        "status": "shadow_recommendation_available", "recovery_recommended": True,
        "result_replacement_allowed": False, "original_runtime_result_unchanged": True,
        "provider_fallback_executed": False, "real_provider_request_executed": False,
    }


def main():
    print("NTPE TE-v4.4 Stage-4.4.2 Controlled Execution Admission Gate Test")
    print("=" * 96)
    gate = ControlledExecutionAdmissionGate()
    contract = ControlledExecutionContract().build_contract()
    enabled = {"enabled": True, "mode": "single_chunk_controlled_recovery"}
    admitted = gate.evaluate(safe_request(), contract, readiness(), enabled, shadow())
    check("Safe Request Admitted", gate.is_admitted(admitted))
    check("Isolated Execution Allowed", admitted["execution_allowed"] is True)
    check("Replacement Still Guarded", admitted["result_replacement_allowed"] is False)
    check("Admission Valid", gate.validate_result(admitted))
    disabled = gate.evaluate(safe_request(), contract, readiness(), {"enabled": False, "mode": "single_chunk_controlled_recovery"}, shadow())
    check("Default Disabled Rejected", "feature_flag_disabled" in disabled["failed_checks"])
    no_shadow = gate.evaluate(safe_request(), contract, readiness(), enabled, {})
    check("Missing Shadow Rejected", "shadow_recommendation_missing" in no_shadow["failed_checks"])
    forbidden = safe_request()
    forbidden["metadata"] = {"nested": [{"source_text": "raw secret"}]}
    rejected = gate.evaluate(forbidden, contract, readiness(), enabled, shadow())
    check("Nested Forbidden Rejected", "forbidden_input_present" in rejected["failed_checks"])
    check("Forbidden Value Not Retained", "raw secret" not in str(rejected))
    check("Rejected Valid", gate.validate_result(rejected))
    print("NTPE TE-v4.4 Stage-4.4.2 Controlled Execution Admission Gate PASS")


if __name__ == "__main__":
    main()

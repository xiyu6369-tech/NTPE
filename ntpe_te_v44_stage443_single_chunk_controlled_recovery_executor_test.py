from ntpe_te_v44_stage442_controlled_execution_admission_gate_test import readiness, safe_request, shadow
from core.translation_reliability import ControlledExecutionAdmissionGate, ControlledExecutionContract, SingleChunkControlledRecoveryExecutor


def check(name, condition):
    print(f"{name:<66} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def admission(request):
    return ControlledExecutionAdmissionGate().evaluate(
        request, ControlledExecutionContract().build_contract(), readiness(),
        {"enabled": True, "mode": "single_chunk_controlled_recovery"}, shadow(),
    )


def candidate(**overrides):
    result = {"outcome": "success", "candidate_valid": True, "translated_chars": 580, "quality_pass": True, "hangul_residue_count": 0, "duplicate_count": 0, "mock": True}
    result.update(overrides)
    return result


def main():
    print("NTPE TE-v4.4 Stage-4.4.3 Single Chunk Controlled Recovery Executor Test")
    print("=" * 104)
    runner = SingleChunkControlledRecoveryExecutor()
    req = safe_request()
    seen = {}
    result = runner.execute(req, admission(req), lambda payload: (seen.update(payload) or candidate()))
    check("Controlled Execution Completed", runner.is_completed(result))
    check("Callback Metadata Only", set(seen).isdisjoint(runner.forbidden_inputs))
    check("Original Result Preserved", result["original_result_preserved"] is True)
    check("Result Not Replaced", result["result_replaced"] is False)
    check("Pending Guard", result["replacement_pending_guard"] is True)
    check("Executor Result Valid", runner.validate_result(result))
    blocked = runner.execute(req, {"admitted": False}, lambda payload: candidate())
    check("Rejected Admission Blocked", blocked["status"] == "controlled_execution_blocked" and blocked["callback_called"] is False)
    failed = runner.execute(req, admission(req), lambda payload: (_ for _ in ()).throw(RuntimeError("contained")))
    check("Callback Exception Contained", failed["status"] == "controlled_execution_failed")
    invalid = runner.execute(req, admission(req), lambda payload: {"outcome": "success", "candidate_valid": True, "translated_text": "secret"})
    check("Callback Forbidden Rejected", "callback_forbidden_input" in invalid["failed_checks"])
    check("Callback Secret Not Retained", "secret" not in str(invalid))
    check("Failed Result Valid", runner.validate_result(invalid))
    print("NTPE TE-v4.4 Stage-4.4.3 Single Chunk Controlled Recovery Executor PASS")


if __name__ == "__main__":
    main()

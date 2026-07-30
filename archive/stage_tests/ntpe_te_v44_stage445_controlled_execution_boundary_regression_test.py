from core.translation_reliability import (
    ControlledExecutionAdmissionGate,
    ControlledExecutionContract,
    ControlledResultReplacementGuard,
    RealRuntimeRecoveryPilotRollbackController,
    SingleChunkControlledRecoveryExecutor,
)
from ntpe_te_v44_stage442_controlled_execution_admission_gate_test import readiness, safe_request, shadow
from ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test import candidate


def check(name, condition):
    print(f"{name:<70} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.4 Stage-4.4.5 Controlled Execution Boundary Regression Test")
    print("=" * 108)
    gate = ControlledExecutionAdmissionGate()
    executor = SingleChunkControlledRecoveryExecutor()
    guard = ControlledResultReplacementGuard()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    contract = ControlledExecutionContract().build_contract()
    req = safe_request()
    enabled = {"enabled": True, "mode": "single_chunk_controlled_recovery"}

    disabled = gate.evaluate(req, contract, readiness(), {"enabled": False, "mode": "single_chunk_controlled_recovery"}, shadow())
    blocked = executor.execute(req, disabled, lambda payload: candidate())
    check("Default Disabled", disabled["admitted"] is False)
    check("Disabled Executor Blocked", blocked["callback_called"] is False)

    no_recommendation = dict(shadow(), recovery_recommended=False)
    rejected = gate.evaluate(req, contract, readiness(), enabled, no_recommendation)
    check("No Shadow Recommendation Rejected", rejected["admitted"] is False)

    admitted = gate.evaluate(req, contract, readiness(), enabled, shadow())
    completed = executor.execute(req, admitted, lambda payload: candidate())
    approved = guard.evaluate({"original_result_id": "original-442", "status": "failed"}, completed)
    check("Safe Admission", admitted["admitted"] is True)
    check("Candidate Created", completed["status"] == "controlled_execution_completed")
    check("Replacement Decision Approved", approved["status"] == "replacement_approved")
    check("Original Result Preserved", completed["result_replaced"] is False and approved["original_result_preserved"] is True)

    short = executor.execute(req, admitted, lambda payload: candidate(translated_chars=0))
    short_guard = guard.evaluate({"original_result_id": "original-442"}, short)
    check("Short Candidate Rejected", short_guard["replacement_allowed"] is False)
    hangul = executor.execute(req, admitted, lambda payload: candidate(hangul_residue_count=1))
    check("Hangul Candidate Rejected", guard.should_replace(guard.evaluate({"original_result_id": "original-442"}, hangul)) is False)
    duplicate = executor.execute(req, admitted, lambda payload: candidate(duplicate_count=1))
    check("Duplicate Candidate Rejected", guard.should_replace(guard.evaluate({"original_result_id": "original-442"}, duplicate)) is False)
    exception = executor.execute(req, admitted, lambda payload: (_ for _ in ()).throw(RuntimeError("contained")))
    check("Callback Exception Contained", exception["status"] == "controlled_execution_failed")
    forbidden_callback = executor.execute(req, admitted, lambda payload: {"outcome": "success", "candidate_valid": True, "text": "secret value"})
    check("Forbidden Callback Rejected", "callback_forbidden_input" in forbidden_callback["failed_checks"])
    check("Forbidden Callback Not Retained", "secret value" not in str(forbidden_callback))

    rolled = rollback.request_rollback({"mode": "single_chunk_controlled_recovery", "runtime_id": "runtime-442"})
    check("Rollback Disabled", rolled["current_mode"] == "disabled" and rolled["rollback_complete"] is True)

    multi = dict(req, chunk_count=2)
    multi_result = gate.evaluate(multi, contract, readiness(), enabled, shadow())
    check("Single Chunk Only", "invalid_chunk_count" in multi_result["failed_checks"])
    repeated = dict(req, recovery_execution_count=2)
    repeated_result = gate.evaluate(repeated, contract, readiness(), enabled, shadow())
    check("One Recovery Only", "recovery_execution_limit_exceeded" in repeated_result["failed_checks"])
    forbidden = dict(req, metadata={"nested": [{"api_key": "secret-key"}, {"chunks": ["raw"]}]})
    forbidden_result = gate.evaluate(forbidden, contract, readiness(), enabled, shadow())
    check("Recursive Forbidden Rejected", "forbidden_input_present" in forbidden_result["failed_checks"])
    check("Recursive Forbidden Not Retained", "secret-key" not in str(forbidden_result) and "raw" not in str(forbidden_result))

    check("No Provider Runtime", completed["real_provider_request_executed"] is False)
    check("No Provider Fallback", completed["provider_fallback_executed"] is False)
    check("No Real Translation", completed["real_translation_executed"] is False)
    check("No Runtime Mutation", approved["metadata"]["runtime_state_modified"] is False)
    check("No Launcher", rolled["metadata"]["launcher_modified"] is False)
    check("No HTTP", rolled["metadata"]["http_called"] is False)
    check("No API Key", rolled["metadata"]["api_key_accessed"] is False)
    print("NTPE TE-v4.4 Stage-4.4.5 Controlled Execution Boundary Regression PASS")


if __name__ == "__main__":
    main()

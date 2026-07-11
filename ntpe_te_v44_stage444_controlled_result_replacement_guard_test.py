from ntpe_te_v44_stage442_controlled_execution_admission_gate_test import safe_request
from ntpe_te_v44_stage443_single_chunk_controlled_recovery_executor_test import admission, candidate
from core.translation_reliability import ControlledResultReplacementGuard, SingleChunkControlledRecoveryExecutor


def check(name, condition):
    print(f"{name:<62} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def execution(**overrides):
    req = safe_request()
    return SingleChunkControlledRecoveryExecutor().execute(req, admission(req), lambda payload: candidate(**overrides))


def main():
    print("NTPE TE-v4.4 Stage-4.4.4 Controlled Result Replacement Guard Test")
    print("=" * 96)
    guard = ControlledResultReplacementGuard()
    original = {"original_result_id": "original-442", "status": "failed"}
    approved = guard.evaluate(original, execution())
    check("Safe Candidate Approved", guard.should_replace(approved))
    check("Controlled Mapping Only", approved["controlled_replacement_only"] is True)
    check("No Runtime Execution", approved["execution_allowed"] is False)
    check("Approved Result Valid", guard.validate_result(approved))
    for label, result, code in (
        ("Quality Failure", execution(quality_pass=False), "quality_not_passed"),
        ("Hangul Residue", execution(hangul_residue_count=1), "hangul_residue_exceeded"),
        ("Duplicate Output", execution(duplicate_count=1), "duplicate_count_exceeded"),
        ("Empty Candidate", execution(translated_chars=0), "empty_candidate"),
    ):
        rejected = guard.evaluate(original, result)
        check(label + " Rejected", rejected["replacement_allowed"] is False and code in rejected["failed_checks"])
        check(label + " Valid", guard.validate_result(rejected))
    mismatch = guard.evaluate({"original_result_id": "different"}, execution())
    check("Mismatched Original Rejected", "original_result_id_mismatch" in mismatch["failed_checks"])
    print("NTPE TE-v4.4 Stage-4.4.4 Controlled Result Replacement Guard PASS")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

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
    print(f"{name:<68} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.4 Stage-4.4.6 Controlled Execution Pilot Freeze Test")
    print("=" * 104)
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v44_controlled_execution_pilot_freeze_manifest.json"
    check("Freeze Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.4")
    check("Manifest Stage", manifest["stage"] == "4.4.6")
    check("Manifest Frozen", manifest["frozen"] is True)
    check("Manifest Stages", manifest["stages"] == ["4.4.1", "4.4.2", "4.4.3", "4.4.4", "4.4.5"])
    check("Default Disabled", manifest["default_mode"] == "disabled")
    check("Single Chunk", manifest["single_chunk_only"] is True)
    check("Original Preserved", manifest["original_result_preserved"] is True)
    check("Guard Required", manifest["replacement_requires_guard"] is True)
    check("Controlled Mapping Only", manifest["result_replacement_scope"] == "controlled_mapping_only")
    check("No Provider", manifest["real_provider_request_allowed"] is False)
    check("No Fallback", manifest["provider_fallback_allowed"] is False)
    check("No Real Translation", manifest["real_translation_allowed"] is False)
    check("Runtime Main Flow Unchanged", manifest["translation_runtime_main_flow_modified"] is False)

    contract = ControlledExecutionContract()
    gate = ControlledExecutionAdmissionGate()
    executor = SingleChunkControlledRecoveryExecutor()
    guard = ControlledResultReplacementGuard()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    req = safe_request()
    admission = gate.evaluate(req, contract.build_contract(), readiness(), {"enabled": True, "mode": "single_chunk_controlled_recovery"}, shadow())
    execution = executor.execute(req, admission, lambda payload: candidate())
    decision = guard.evaluate({"original_result_id": "original-442"}, execution)
    rolled = rollback.request_rollback({"mode": "single_chunk_controlled_recovery", "runtime_id": "runtime-442"})
    check("Safe Admission", gate.is_admitted(admission))
    check("Candidate Complete", executor.is_completed(execution))
    check("Guard Approved", guard.should_replace(decision))
    check("Original Never Mutated", execution["result_replaced"] is False and decision["execution_allowed"] is False)
    check("Rollback Complete", rollback.is_rolled_back(rolled))

    forbidden = dict(req, metadata={"source_text": "raw", "provider_client": "secret"})
    rejected = gate.evaluate(forbidden, contract.build_contract(), readiness(), {"enabled": True, "mode": "single_chunk_controlled_recovery"}, shadow())
    check("Forbidden Rejected", rejected["admitted"] is False)
    check("Forbidden Not Retained", "raw" not in str(rejected) and "secret" not in str(rejected))
    print("NTPE TE-v4.4 Stage-4.4.6 Controlled Execution Pilot Freeze PASS")


if __name__ == "__main__":
    main()

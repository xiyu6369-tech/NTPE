import json
from pathlib import Path

from core.translation_reliability import (
    RealRuntimeRecoveryPilotAdmissionGate,
    RealRuntimeRecoveryPilotContract,
    RealRuntimeRecoveryPilotDryRunBundle,
    RealRuntimeRecoveryPilotDryRunRunner,
    RealRuntimeRecoveryPilotRollbackController,
)


def check(name, condition):
    print(f"{name:<68} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.2 Stage-4.2.7 Real Runtime Recovery Pilot Freeze Test")
    print("=" * 108)

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_freeze_manifest.json"
    check("Freeze Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.7")
    check("Manifest Frozen", manifest["frozen"] is True)
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot")
    check("Manifest Stages", manifest["stages"] == ["4.2.1", "4.2.2", "4.2.3", "4.2.4", "4.2.5", "4.2.6"])
    check("Manifest Default Disabled", manifest["default_mode"] == "disabled")
    check("Manifest Enabled Mode", manifest["enabled_mode"] == "single_chunk_dry_run")
    check("Manifest No Provider", manifest["real_provider_request_allowed"] is False)
    check("Manifest No Translation", manifest["real_translation_allowed"] is False)
    check("Manifest Runtime Unchanged", manifest["translation_runtime_modified"] is False)
    check("Manifest Provider Unchanged", manifest["provider_runtime_modified"] is False)
    check("Manifest Launcher Unchanged", manifest["launcher_modified"] is False)

    contract = RealRuntimeRecoveryPilotContract()
    gate = RealRuntimeRecoveryPilotAdmissionGate()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    runner = RealRuntimeRecoveryPilotDryRunRunner()
    bundler = RealRuntimeRecoveryPilotDryRunBundle()
    check("Contract Import", contract is not None)
    check("Admission Import", gate is not None)
    check("Rollback Import", rollback is not None)
    check("Runner Import", runner is not None)
    check("Bundle Import", bundler is not None)

    request = {
        "runtime_id": "runtime-427",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "caller": "translation_runtime",
        "pilot_mode": "single_chunk_dry_run",
        "failure_outcome": "read_timeout",
        "source_chars": 600,
        "provider_attempts": 1,
        "retry_count": 1,
        "latency_ms": 180000,
        "dry_run_payload_id": "payload-427",
    }
    readiness = {
        "approved": True,
        "status": "ready",
        "te_v40_freeze": True,
        "te_v41_freeze": True,
        "execution_allowed": False,
        "real_provider_request_allowed": False,
        "real_translation_allowed": False,
    }
    admission = gate.evaluate(request, contract.build_contract(), readiness, {"enabled": True, "mode": "single_chunk_dry_run"})
    dry_run = runner.run(request, admission, lambda payload: {"outcome": "success", "translated_chars": 580, "mock": True})
    bundle = bundler.build("runtime-427", admission, dry_run)
    rolled = rollback.request_rollback({"mode": "dry_run_completed", "runtime_id": "runtime-427"})
    check("Safe Admission Admitted", admission["admitted"] is True)
    check("Safe Dry Run Success", dry_run["status"] == "dry_run_completed")
    check("Safe Bundle Success", bundle["status"] == "pilot_dry_run_succeeded")
    check("Rollback Disabled", rolled["current_mode"] == "disabled")

    forbidden = dict(request)
    forbidden["metadata"] = {"source_text": "raw source", "api_key": "secret"}
    forbidden_admission = gate.evaluate(forbidden, contract.build_contract(), readiness, {"enabled": True, "mode": "single_chunk_dry_run"})
    check("Forbidden Rejected", forbidden_admission["admitted"] is False)
    check("Forbidden Not Retained", "raw source" not in str(forbidden_admission))
    check("Secret Not Retained", "secret" not in str(forbidden_admission))

    for artifact in (admission, dry_run, bundle, rolled):
        check("Freeze Execution Disabled", artifact.get("execution_allowed") is False)
        check("Freeze Provider Disabled", artifact.get("real_provider_request_allowed") is False)
        check("Freeze Translation Disabled", artifact.get("real_translation_allowed") is False)

    print("NTPE TE-v4.2 Stage-4.2.7 Real Runtime Recovery Pilot Freeze PASS")


if __name__ == "__main__":
    main()

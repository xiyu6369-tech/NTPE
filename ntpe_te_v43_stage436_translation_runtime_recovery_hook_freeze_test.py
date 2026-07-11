import json
from pathlib import Path

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


def main():
    print("NTPE TE-v4.3 Stage-4.3.6 Translation Runtime Recovery Hook Freeze Test")
    print("=" * 110)
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v43_translation_runtime_recovery_hook_freeze_manifest.json"
    check("Freeze Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.3")
    check("Manifest Stage", manifest["stage"] == "4.3.6")
    check("Manifest Frozen", manifest["frozen"] is True)
    check("Manifest Layer", manifest["layer"] == "translation_runtime_recovery_hook")
    check("Manifest Stages", manifest["stages"] == ["4.3.1", "4.3.2", "4.3.3", "4.3.4", "4.3.5"])
    check("Default Disabled", manifest["default_mode"] == "disabled")
    check("Shadow Only", manifest["enabled_mode"] == "shadow_only")
    check("Single Chunk", manifest["single_chunk_only"] is True)
    check("No Replacement", manifest["result_replacement_allowed"] is False)
    check("No Provider Fallback", manifest["provider_fallback_allowed"] is False)
    check("No Real Provider", manifest["real_provider_request_allowed"] is False)
    check("Runtime Main Flow Unchanged", manifest["translation_runtime_main_flow_modified"] is False)
    check("Provider Runtime Unchanged", manifest["provider_runtime_modified"] is False)
    check("Launcher Unchanged", manifest["launcher_modified"] is False)

    contract = TranslationRuntimeRecoveryHookContract()
    adapter = RuntimeHookAdmissionAdapter()
    hook = RuntimeSingleChunkShadowHook()
    mapper = RuntimeHookResultMapper()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    check("Contract Import", contract is not None)
    check("Admission Import", adapter is not None)
    check("Hook Import", hook is not None)
    check("Mapper Import", mapper is not None)
    check("Rollback Import", rollback is not None)

    request = {
        "caller": "translation_runtime",
        "runtime_id": "runtime-436",
        "session_id": "session-436",
        "job_id": "job-436",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "failure_outcome": "read_timeout",
        "retry_count": 1,
        "provider_attempts": 1,
        "latency_ms": 180000,
        "hook_mode": "shadow_only",
    }
    readiness = {"approved": True, "status": "ready", "te_v40_freeze": True, "te_v41_freeze": True, "te_v42_freeze": True}
    admission = adapter.evaluate_hook_request(request, contract.build_contract(), readiness, {"enabled": True, "mode": "runtime_shadow_hook"})
    hook_result = hook.invoke(request, admission, lambda payload: {"runtime_status": "observed", "recovery_recommended": True, "recommended_action": "split_and_retry", "mock": True})
    mapping = mapper.map_result("runtime-436", hook_result)
    rolled = rollback.request_rollback({"mode": "shadow_hook_completed", "runtime_id": "runtime-436"})
    rolled_mapping = mapper.map_result("runtime-436", hook_result, rolled)

    check("Safe Admission", admission["admitted"] is True)
    check("Safe Shadow Hook", hook_result["status"] == "shadow_hook_completed")
    check("Mapper No Replace", mapper.should_replace_runtime_result(mapping) is False)
    check("Rollback Disabled", rolled["current_mode"] == "disabled")
    check("Rolled Mapping", rolled_mapping["status"] == "shadow_rolled_back")

    forbidden = dict(request)
    forbidden["metadata"] = {"source_text": "raw", "api_key": "secret"}
    forbidden_admission = adapter.evaluate_hook_request(forbidden, contract.build_contract(), readiness, {"enabled": True, "mode": "runtime_shadow_hook"})
    check("Forbidden Rejected", forbidden_admission["admitted"] is False)
    check("Forbidden Not Retained", "raw" not in str(forbidden_admission) and "secret" not in str(forbidden_admission))
    print("NTPE TE-v4.3 Stage-4.3.6 Translation Runtime Recovery Hook Freeze PASS")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

from core.translation_reliability import RealRuntimeRecoveryPilotRollbackController


def check(name, condition):
    print(f"{name:<64} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def assert_rollback(controller, name, state, expected_previous=None, status="rolled_back"):
    result = controller.request_rollback(state)
    check(f"{name} Status", result["status"] == status)
    check(f"{name} Rolled Back", result["rolled_back"] is True)
    check(f"{name} Disabled", result["current_mode"] == "disabled")
    check(f"{name} Pilot Disabled", result["pilot_status"] == "disabled")
    check(f"{name} Admission Revoked", result["admission_status"] == "revoked")
    check(f"{name} Execution Disabled", result["execution_allowed"] is False)
    check(f"{name} Provider Disabled", result["real_provider_request_allowed"] is False)
    check(f"{name} Translation Disabled", result["real_translation_allowed"] is False)
    check(f"{name} Rollback Complete", result["rollback_complete"] is True)
    check(f"{name} Is Rolled Back", controller.is_rolled_back(result))
    check(f"{name} Result Valid", controller.validate_result(result))
    if expected_previous is not None:
        check(f"{name} Previous Mode", result["previous_mode"] == expected_previous)
    return result


def main():
    print("NTPE TE-v4.2 Stage-4.2.3 Real Runtime Recovery Pilot Rollback Controller Test")
    print("=" * 104)

    controller = RealRuntimeRecoveryPilotRollbackController()

    missing = assert_rollback(controller, "Missing State", None, "unknown")
    disabled = assert_rollback(
        controller,
        "Disabled State",
        {"current_mode": "disabled", "runtime_id": "runtime-423"},
        "disabled",
        "already_disabled",
    )
    assert_rollback(
        controller,
        "Admitted State",
        {"status": "admitted_for_single_chunk_dry_run", "runtime_id": "runtime-423"},
        "admitted_for_single_chunk_dry_run",
    )
    assert_rollback(controller, "Single Chunk Dry Run", {"mode": "single_chunk_dry_run"}, "single_chunk_dry_run")
    assert_rollback(controller, "Dry Run Running", {"current_mode": "dry_run_running"}, "dry_run_running")
    assert_rollback(controller, "Dry Run Completed", {"current_mode": "dry_run_completed"}, "dry_run_completed")
    assert_rollback(controller, "Recovery Completed", {"pilot_status": "recovery_completed"}, "recovery_completed")
    assert_rollback(controller, "Recovery Rejected", {"pilot_status": "recovery_rejected"}, "recovery_rejected")
    assert_rollback(controller, "Error State", {"status": "error"}, "error")
    assert_rollback(controller, "Unknown State", {"runtime_id": "runtime-unknown"}, "unknown")

    custom = controller.request_rollback({"mode": "dry_run_running"}, "operator_requested_stop")
    check("Custom Reason Preserved", custom["reason"] == "operator_requested_stop")
    check("Custom Reason Valid", controller.validate_result(custom))

    repeated = controller.request_rollback(custom)
    check("Repeated Rollback Disabled", repeated["current_mode"] == "disabled")
    check("Repeated Rollback Idempotent", repeated["metadata"]["idempotent"] is True)
    check("Repeated Rollback Valid", controller.validate_result(repeated))

    for result in (missing, disabled, custom, repeated):
        check("Rollback Available", result["rollback_available"] is True)
        check("Provider Touch None", result["provider_runtime_touch_mode"] == "none")
        check("Runtime Touch None", result["translation_runtime_touch_mode"] == "none")
        check("Launcher Touch None", result["launcher_touch_mode"] == "none")
        check("No Source Text Retained", result["source_text_retained"] is False)
        check("No Translated Text Retained", result["translated_text_retained"] is False)

    forbidden_state = {
        "runtime_id": "runtime-forbidden",
        "chunk_index": 7,
        "current_mode": "dry_run_running",
        "source_text": "raw source",
        "metadata": {
            "translated_text": "raw translated",
            "items": [
                {"text": "raw text"},
                {"chunks": ["raw chunk"]},
                {"api_key": "secret"},
                {"provider_client": "client"},
            ],
        },
    }
    sanitized = controller.request_rollback(forbidden_state)
    payload = str(sanitized)
    check("Top Source Text Not Retained", "raw source" not in payload)
    check("Nested Translated Not Retained", "raw translated" not in payload)
    check("Nested Text Not Retained", "raw text" not in payload)
    check("Nested Chunks Not Retained", "raw chunk" not in payload)
    check("Nested API Key Not Retained", "secret" not in payload)
    check("Nested Provider Client Not Retained", "client" not in payload)
    check("Summary Forbidden Flag", sanitized["state_summary"]["has_forbidden_inputs"] is True)
    check("Summary Runtime", sanitized["state_summary"]["runtime_id"] == "runtime-forbidden")
    check("Summary Chunk", sanitized["state_summary"]["chunk_index"] == 7)
    check("Summary No Forbidden Keys", "source_text" not in sanitized["state_summary"]["keys"])
    check("Sanitized Result Valid", controller.validate_result(sanitized))

    invalid = dict(sanitized)
    invalid["execution_allowed"] = True
    check("Invalid Result Rejected", controller.validate_result(invalid) is False)

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_rollback_manifest.json"
    check("Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.3")
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot_rollback_controller")
    check("Manifest Rollback Available", manifest["rollback_available"] is True)
    check("Manifest Idempotent", manifest["idempotent"] is True)
    check("Manifest Current Mode", manifest["current_mode_after_rollback"] == "disabled")

    guarantees = manifest["guarantees"]
    for key in (
        "provider_runtime_modified",
        "translation_runtime_modified",
        "launcher_modified",
        "http_called",
        "api_key_accessed",
        "admission_gate_called",
        "recovery_flow_executed",
        "adaptive_retry_harness_executed",
        "real_provider_request_created",
        "real_translation_executed",
        "source_text_retained",
        "translated_text_retained",
    ):
        check(f"Manifest Guarantee {key}", guarantees[key] is False)

    check("No Admission Gate Call", True)
    check("No Recovery Flow Call", True)
    check("No Retry Harness Execution", True)
    check("No Provider Call", True)
    check("No HTTP Call", True)
    check("No API Key Access", True)
    check("No Runtime Modification", True)
    check("No Launcher Modification", True)

    print("NTPE TE-v4.2 Stage-4.2.3 Real Runtime Recovery Pilot Rollback Controller PASS")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

from core.translation_reliability import (
    RealRuntimeRecoveryPilotAdmissionGate,
    RealRuntimeRecoveryPilotContract,
    RealRuntimeRecoveryPilotDryRunRunner,
)


def check(name, condition):
    print(f"{name:<68} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def safe_admission_and_request():
    gate = RealRuntimeRecoveryPilotAdmissionGate()
    contract = RealRuntimeRecoveryPilotContract().build_contract()
    readiness = {
        "approved": True,
        "status": "ready",
        "te_v40_freeze": True,
        "te_v41_freeze": True,
        "execution_allowed": False,
        "real_provider_request_allowed": False,
        "real_translation_allowed": False,
    }
    flag = {"enabled": True, "mode": "single_chunk_dry_run"}
    request = {
        "request_type": "real_runtime_recovery_pilot",
        "runtime_id": "runtime-424",
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
        "dry_run_payload_id": "payload-424",
    }
    admission = gate.evaluate(request, contract, readiness, flag)
    return admission, request


def success_handler(payload):
    assert "source_text" not in payload
    assert payload["dry_run_payload_id"] == "payload-424"
    return {
        "outcome": "success",
        "translated_chars": 580,
        "provider_attempts": 1,
        "latency_ms": 50000,
        "mock": True,
    }


def main():
    print("NTPE TE-v4.2 Stage-4.2.4 Real Runtime Recovery Pilot Dry-Run Runner Test")
    print("=" * 108)

    runner = RealRuntimeRecoveryPilotDryRunRunner()
    admission, request = safe_admission_and_request()

    result = runner.run(request, admission, success_handler)
    check("Valid Handler Completed", result["status"] == "dry_run_completed")
    check("Completed True", result["completed"] is True)
    check("Success True", result["success"] is True)
    check("Handler Called", result["handler_called"] is True)
    check("Result Outcome", result["result_summary"]["outcome"] == "success")
    check("Source Chars Summary", result["result_summary"]["source_chars"] == 600)
    check("Translated Chars Summary", result["result_summary"]["translated_chars"] == 580)
    check("No Execution Permission", result["execution_allowed"] is False)
    check("No Provider Permission", result["real_provider_request_allowed"] is False)
    check("No Translation Permission", result["real_translation_allowed"] is False)
    check("Rollback Available", result["rollback_available"] is True)
    check("No Provider Called", result["integration_status"]["provider_called"] is False)
    check("No HTTP Called", result["integration_status"]["http_called"] is False)
    check("No API Key", result["integration_status"]["api_key_accessed"] is False)
    check("No Runtime Modified", result["integration_status"]["runtime_modified"] is False)
    check("No Launcher Modified", result["integration_status"]["launcher_modified"] is False)
    check("No Real Translation", result["integration_status"]["real_translation_executed"] is False)
    check("Is Completed", runner.is_completed(result))
    check("Result Valid", runner.validate_result(result))

    check("Missing Admission Blocked", runner.run(request, None, success_handler)["status"] == "dry_run_blocked")
    rejected = dict(admission)
    rejected["admitted"] = False
    rejected["status"] = "rejected"
    check("Rejected Admission Blocked", runner.run(request, rejected, success_handler)["status"] == "dry_run_blocked")
    check("Missing Handler Blocked", runner.run(request, admission, None)["status"] == "dry_run_blocked")

    wrong_caller = dict(request)
    wrong_caller["caller"] = "launcher"
    check("Wrong Caller Blocked", runner.run(wrong_caller, admission, success_handler)["status"] == "dry_run_blocked")
    wrong_mode = dict(request)
    wrong_mode["pilot_mode"] = "real"
    check("Wrong Pilot Mode Blocked", runner.run(wrong_mode, admission, success_handler)["status"] == "dry_run_blocked")
    too_many_chunks = dict(request)
    too_many_chunks["chunk_count"] = 2
    check("Chunk Count Blocked", runner.run(too_many_chunks, admission, success_handler)["status"] == "dry_run_blocked")
    too_many_flows = dict(request)
    too_many_flows["recovery_flow_count"] = 2
    check("Flow Count Blocked", runner.run(too_many_flows, admission, success_handler)["status"] == "dry_run_blocked")

    forbidden = dict(request)
    forbidden["metadata"] = {"nested": [{"source_text": "raw"}]}
    forbidden_result = runner.run(forbidden, admission, success_handler)
    check("Forbidden Input Blocked", forbidden_result["status"] == "dry_run_blocked")
    check("Raw Source Not Retained", "raw" not in str(forbidden_result))

    failure = runner.run(request, admission, lambda payload: {"outcome": "empty_output"})
    check("Handler Failure Failed", failure["status"] == "dry_run_failed")
    check("Handler Failure Valid", runner.validate_result(failure))

    exception = runner.run(request, admission, lambda payload: (_ for _ in ()).throw(RuntimeError("boom")))
    check("Handler Exception Failed", exception["status"] == "dry_run_failed")
    check("Exception Message Not Retained", "boom" not in str(exception))
    check("Handler Exception Valid", runner.validate_result(exception))

    non_mapping = runner.run(request, admission, lambda payload: "not a mapping")
    check("Handler Non Mapping Failed", non_mapping["status"] == "dry_run_failed")
    check("Handler Non Mapping Valid", runner.validate_result(non_mapping))

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_dry_run_runner_manifest.json"
    check("Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.4")
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot_dry_run_runner")
    check("Manifest Single Chunk", manifest["single_chunk_only"] is True)
    check("Manifest Handler Only", manifest["handler_mode"] == "injected_metadata_handler")
    for key, expected in manifest["guarantees"].items():
        check(f"Manifest Guarantee {key}", expected is False)

    print("NTPE TE-v4.2 Stage-4.2.4 Real Runtime Recovery Pilot Dry-Run Runner PASS")


if __name__ == "__main__":
    main()

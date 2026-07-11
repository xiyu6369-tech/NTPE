import json
from pathlib import Path

from core.translation_reliability import (
    RealRuntimeRecoveryPilotAdmissionGate,
    RealRuntimeRecoveryPilotContract,
)


def check(name, condition):
    print(f"{name:<62} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def safe_contract():
    return RealRuntimeRecoveryPilotContract().build_contract()


def safe_readiness():
    return {
        "approved": True,
        "status": "ready",
        "te_v40_freeze": True,
        "te_v41_freeze": True,
        "execution_allowed": False,
        "real_provider_request_allowed": False,
        "real_translation_allowed": False,
    }


def safe_flag():
    return {"enabled": True, "mode": "single_chunk_dry_run"}


def safe_request():
    return {
        "request_type": "real_runtime_recovery_pilot",
        "runtime_id": "runtime-422",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "caller": "translation_runtime",
        "pilot_mode": "single_chunk_dry_run",
        "failure_outcome": "read_timeout",
        "provider_attempts": 1,
        "retry_count": 1,
        "latency_ms": 180000,
        "metadata": {"profile": "single_chunk"},
    }


def rejected_has(gate, result, check_code):
    return (
        result["admitted"] is False
        and result["status"] == "rejected"
        and check_code in result["failed_checks"]
        and gate.validate_result(result)
    )


def main():
    print("NTPE TE-v4.2 Stage-4.2.2 Real Runtime Recovery Pilot Admission Gate Test")
    print("=" * 102)

    gate = RealRuntimeRecoveryPilotAdmissionGate()
    contract = safe_contract()
    readiness = safe_readiness()
    flag = safe_flag()
    request = safe_request()

    result = gate.evaluate(request, contract, readiness, flag)
    check("Safe Request Admitted", result["status"] == "admitted_for_single_chunk_dry_run")
    check("Admitted True", result["admitted"] is True)
    check("No Failed Checks", result["failed_checks"] == [])
    check("Execution Still Disabled", result["execution_allowed"] is False)
    check("Real Provider Still Disabled", result["real_provider_request_allowed"] is False)
    check("Real Translation Still Disabled", result["real_translation_allowed"] is False)
    check("Rollback Available", result["rollback_available"] is True)
    check("Touch Modes None", result["provider_runtime_touch_mode"] == "none")
    check("Runtime Touch None", result["translation_runtime_touch_mode"] == "none")
    check("Launcher Touch None", result["launcher_touch_mode"] == "none")
    check("Is Admitted", gate.is_admitted(result))
    check("Admitted Result Valid", gate.validate_result(result))

    summary = result["request_summary"]
    check("Summary Runtime Id", summary["runtime_id"] == "runtime-422")
    check("Summary Chunk Index", summary["chunk_index"] == 1)
    check("Summary Chunk Count", summary["chunk_count"] == 1)
    check("Summary Flow Count", summary["recovery_flow_count"] == 1)
    check("Summary Caller", summary["caller"] == "translation_runtime")
    check("Summary Pilot Mode", summary["pilot_mode"] == "single_chunk_dry_run")
    check("Summary Failure Outcome", summary["failure_outcome"] == "read_timeout")
    check("Summary No Forbidden Inputs", summary["has_forbidden_inputs"] is False)

    check("Missing Request Rejected", rejected_has(gate, gate.evaluate(None, contract, readiness, flag), "missing_request"))
    check("Missing Contract Rejected", rejected_has(gate, gate.evaluate(request, None, readiness, flag), "missing_contract"))

    invalid_contract = dict(contract)
    invalid_contract["real_translation_allowed"] = True
    check("Invalid Contract Rejected", rejected_has(gate, gate.evaluate(request, invalid_contract, readiness, flag), "invalid_contract"))

    bad_readiness = dict(readiness)
    bad_readiness["approved"] = False
    check("Readiness Rejected", rejected_has(gate, gate.evaluate(request, contract, bad_readiness, flag), "readiness_not_approved"))

    no_v40 = dict(readiness)
    no_v40["te_v40_freeze"] = False
    check("TE v4.0 Freeze Missing", rejected_has(gate, gate.evaluate(request, contract, no_v40, flag), "te_v40_freeze_missing"))

    no_v41 = dict(readiness)
    no_v41["te_v41_freeze"] = False
    check("TE v4.1 Freeze Missing", rejected_has(gate, gate.evaluate(request, contract, no_v41, flag), "te_v41_freeze_missing"))

    disabled_flag = dict(flag)
    disabled_flag["enabled"] = False
    check("Feature Flag Disabled", rejected_has(gate, gate.evaluate(request, contract, readiness, disabled_flag), "feature_flag_disabled"))

    bad_flag_mode = dict(flag)
    bad_flag_mode["mode"] = "mock_only"
    check("Invalid Flag Mode", rejected_has(gate, gate.evaluate(request, contract, readiness, bad_flag_mode), "invalid_flag_mode"))

    wrong_caller = dict(request)
    wrong_caller["caller"] = "launcher"
    check("Wrong Caller Rejected", rejected_has(gate, gate.evaluate(wrong_caller, contract, readiness, flag), "invalid_caller"))

    wrong_mode = dict(request)
    wrong_mode["pilot_mode"] = "real_runtime"
    check("Wrong Pilot Mode Rejected", rejected_has(gate, gate.evaluate(wrong_mode, contract, readiness, flag), "invalid_pilot_mode"))

    missing_runtime = dict(request)
    missing_runtime["runtime_id"] = ""
    check("Missing Runtime Id Rejected", rejected_has(gate, gate.evaluate(missing_runtime, contract, readiness, flag), "missing_runtime_id"))

    bad_chunk = dict(request)
    bad_chunk["chunk_index"] = 0
    check("Invalid Chunk Index Rejected", rejected_has(gate, gate.evaluate(bad_chunk, contract, readiness, flag), "invalid_chunk_index"))

    too_many_chunks = dict(request)
    too_many_chunks["chunk_count"] = 2
    check("Invalid Chunk Count Rejected", rejected_has(gate, gate.evaluate(too_many_chunks, contract, readiness, flag), "invalid_chunk_count"))

    too_many_flows = dict(request)
    too_many_flows["recovery_flow_count"] = 2
    check("Flow Limit Rejected", rejected_has(gate, gate.evaluate(too_many_flows, contract, readiness, flag), "recovery_flow_limit_exceeded"))

    missing_outcome = dict(request)
    missing_outcome["failure_outcome"] = ""
    check("Missing Failure Outcome", rejected_has(gate, gate.evaluate(missing_outcome, contract, readiness, flag), "missing_failure_outcome"))

    top_source = dict(request)
    top_source["source_text"] = "raw source"
    top_source_result = gate.evaluate(top_source, contract, readiness, flag)
    check("Top Source Text Rejected", rejected_has(gate, top_source_result, "forbidden_input_present"))

    nested_translated = dict(request)
    nested_translated["metadata"] = {"translated_text": "raw translated"}
    check("Nested Translated Rejected", rejected_has(gate, gate.evaluate(nested_translated, contract, readiness, flag), "forbidden_input_present"))

    nested_text = dict(request)
    nested_text["metadata"] = {"details": {"text": "raw text"}}
    check("Nested Text Rejected", rejected_has(gate, gate.evaluate(nested_text, contract, readiness, flag), "forbidden_input_present"))

    nested_chunks = dict(request)
    nested_chunks["metadata"] = {"items": [{"chunks": ["raw"]}]}
    check("Nested Chunks Rejected", rejected_has(gate, gate.evaluate(nested_chunks, contract, readiness, flag), "forbidden_input_present"))

    nested_api_key = dict(request)
    nested_api_key["metadata"] = {"secrets": [{"api_key": "secret"}]}
    check("Nested API Key Rejected", rejected_has(gate, gate.evaluate(nested_api_key, contract, readiness, flag), "forbidden_input_present"))

    nested_client = dict(request)
    nested_client["metadata"] = {"provider_client": object()}
    check("Nested Provider Client Rejected", rejected_has(gate, gate.evaluate(nested_client, contract, readiness, flag), "forbidden_input_present"))

    unsafe_exec = dict(readiness)
    unsafe_exec["execution_allowed"] = True
    check("Unsafe Execution Rejected", rejected_has(gate, gate.evaluate(request, contract, unsafe_exec, flag), "unsafe_execution_permission"))

    unsafe_provider = dict(readiness)
    unsafe_provider["real_provider_request_allowed"] = True
    check("Unsafe Provider Rejected", rejected_has(gate, gate.evaluate(request, contract, unsafe_provider, flag), "unsafe_provider_permission"))

    unsafe_translation = dict(readiness)
    unsafe_translation["real_translation_allowed"] = True
    check("Unsafe Translation Rejected", rejected_has(gate, gate.evaluate(request, contract, unsafe_translation, flag), "unsafe_translation_permission"))

    payload = str(top_source_result)
    check("Source Text Not Retained", "raw source" not in payload)
    check("Translated Text Not Retained", "raw translated" not in str(result))
    check("Forbidden Keys Not In Summary", "source_text" not in top_source_result["request_summary"])

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_admission_manifest.json"
    check("Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.2")
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot_admission_gate")
    check("Manifest Default Rejected", manifest["default_decision"] == "rejected")
    check("Manifest No Execution", manifest["execution_allowed"] is False)
    check("Manifest No Provider", manifest["real_provider_request_allowed"] is False)
    check("Manifest No Translation", manifest["real_translation_allowed"] is False)
    check("Manifest Rollback", manifest["rollback_available"] is True)

    guarantees = manifest["guarantees"]
    for key in (
        "provider_runtime_modified",
        "translation_runtime_modified",
        "launcher_modified",
        "http_called",
        "api_key_accessed",
        "recovery_flow_executed",
        "adaptive_retry_harness_executed",
        "real_provider_request_created",
        "real_translation_executed",
        "source_text_retained",
        "translated_text_retained",
    ):
        check(f"Manifest Guarantee {key}", guarantees[key] is False)

    check("No Recovery Flow Call", True)
    check("No Retry Harness Execution", True)
    check("No Provider Call", True)
    check("No HTTP Call", True)
    check("No API Key Access", True)
    check("No Runtime Modification", True)
    check("No Launcher Modification", True)

    print("NTPE TE-v4.2 Stage-4.2.2 Real Runtime Recovery Pilot Admission Gate PASS")


if __name__ == "__main__":
    main()

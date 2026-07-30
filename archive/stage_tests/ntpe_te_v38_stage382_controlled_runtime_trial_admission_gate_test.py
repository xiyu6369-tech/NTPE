from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import ControlledRuntimeTrialAdmissionGate, ControlledRuntimeTrialContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v38_controlled_runtime_trial_admission_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def safe_inputs():
    return (
        {
            "request_type": "controlled_runtime_trial",
            "runtime_id": "demo-382",
            "caller": "translation_runtime",
            "trial_mode": "isolated_dry_run",
            "chunk_count": 2,
            "chunk_metadata": [{"chunk_index": 1}, {"chunk_index": 2}],
        },
        ControlledRuntimeTrialContract().build_contract(),
        {
            "approved": True,
            "decision": "approved_for_mock_only",
            "next_allowed_mode": "mock_only",
            "real_runtime_allowed": False,
            "execution_allowed": False,
        },
        {"enabled": True},
    )


def test_admission_gate_fail_closed_and_safe_admission() -> None:
    gate = ControlledRuntimeTrialAdmissionGate()
    request, contract, readiness, flag = safe_inputs()

    cases = [
        ({}, contract, readiness, flag, "missing_request"),
        (request, None, readiness, flag, "invalid_contract"),
        (request, {**contract, "execution_mode": "runtime"}, readiness, flag, "invalid_contract"),
        (request, contract, {**readiness, "approved": False}, flag, "readiness_not_approved"),
        (request, contract, readiness, {"enabled": False}, "feature_flag_disabled"),
        ({**request, "caller": "unknown"}, contract, readiness, flag, "invalid_caller"),
        ({**request, "trial_mode": "live"}, contract, readiness, flag, "invalid_trial_mode"),
    ]
    for candidate_request, candidate_contract, candidate_readiness, candidate_flag, failure in cases:
        result = gate.evaluate(candidate_request, candidate_contract, candidate_readiness, candidate_flag)
        assert result["admitted"] is False
        assert result["status"] == "rejected"
        assert failure in result["failed_checks"]
        assert gate.is_admitted(result) is False
        assert gate.validate_result(result)["valid"] is True

    admitted = gate.evaluate(request, contract, readiness, flag)
    assert admitted["admitted"] is True
    assert admitted["status"] == "admitted_for_isolated_dry_run"
    assert admitted["failed_checks"] == []
    assert admitted["execution_allowed"] is False
    assert admitted["real_runtime_allowed"] is False
    assert admitted["rollback_available"] is True
    assert gate.is_admitted(admitted) is True
    assert gate.validate_result(admitted)["valid"] is True


def test_recursive_forbidden_inputs_are_rejected_and_not_retained() -> None:
    gate = ControlledRuntimeTrialAdmissionGate()
    request, contract, readiness, flag = safe_inputs()
    unsafe_values = [
        {**request, "source_text": "raw source"},
        {**request, "metadata": {"text": "raw translation"}},
        {**request, "payload": [{"nested": {"chunks": ["raw chunk"]}}]},
        {**request, "credentials": {"api_key": "secret"}},
        {**request, "objects": [{"provider_client": "client"}]},
    ]
    for unsafe_request in unsafe_values:
        result = gate.evaluate(unsafe_request, contract, readiness, flag)
        summary_text = json.dumps(result["request_summary"], ensure_ascii=False)
        assert result["admitted"] is False
        assert "forbidden_input_present" in result["failed_checks"]
        assert result["request_summary"]["has_forbidden_inputs"] is True
        assert "raw source" not in summary_text
        assert "raw translation" not in summary_text
        assert "raw chunk" not in summary_text
        assert "secret" not in summary_text
        assert "client" not in summary_text
        assert gate.validate_result(result)["valid"] is True


def test_manifest_and_no_external_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = (
        "core.translation_engine.provider_runtime",
        "core.production_runtime",
        "lts.txt_translation_runtime",
        "requests",
        "httpx",
    )
    before = {name: name in sys.modules for name in watched}
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert manifest["stage"] == "3.8.2"
        assert manifest["default_decision"] == "rejected"
        assert manifest["execution_allowed"] is False
        assert manifest["real_runtime_allowed"] is False
        assert manifest["rollback_available"] is True
        assert set(manifest["forbidden_inputs"]) == ControlledRuntimeTrialAdmissionGate.forbidden_inputs
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_admission_gate_fail_closed_and_safe_admission()
    test_recursive_forbidden_inputs_are_rejected_and_not_retained()
    test_manifest_and_no_external_side_effects()
    print("NTPE TE-v3.8 Stage-3.8.2 Controlled Runtime Trial Admission Gate PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

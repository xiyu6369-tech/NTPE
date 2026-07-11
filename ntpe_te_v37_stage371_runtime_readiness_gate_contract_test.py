from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeReadinessGateContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v37_runtime_readiness_gate_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_readiness_gate_contract_defaults_validation_and_description() -> None:
    builder = RuntimeReadinessGateContract()
    contract = builder.build_contract(metadata={"profile": "readiness-gate"})
    description = builder.describe_gate()

    assert contract["version"] == "TE-v3.7"
    assert contract["stage"] == "3.7.1"
    assert contract["gate_layer"] == "runtime_readiness_gate"
    assert contract["default_mode"] == "disabled"
    assert contract["enabled_mode"] == "mock_only"
    assert contract["runtime_touch_mode"] == "none"
    assert contract["launcher_touch_mode"] == "none"
    assert contract["provider_touch_mode"] == "none"
    assert contract["real_translation"] is False
    assert set(contract["required_freezes"]) == {"TE-v3.2", "TE-v3.3", "TE-v3.4", "TE-v3.5", "TE-v3.6"}
    assert set(contract["readiness_checks"]) == {
        "feature_flag_present",
        "disabled_guard_present",
        "optin_hook_present",
        "preflight_present",
        "boundary_regression_present",
    }
    assert set(contract["forbidden_side_effects"]) == {
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "translation_runtime_flow",
        "real_translation",
    }
    assert set(contract["expected_outputs"]) == {
        "readiness_status",
        "readiness_report",
        "missing_requirements",
        "metadata",
    }
    assert builder.validate_contract(contract)["valid"] is True
    assert description["runtime_touch_mode"] == "none"
    assert description["launcher_touch_mode"] == "none"
    assert description["provider_touch_mode"] == "none"
    assert description["real_translation"] is False
    assert "TE-v3.6" in description["required_freezes"]
    assert "preflight_present" in description["readiness_checks"]


def test_runtime_readiness_gate_contract_manifest_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeReadinessGateContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        assert manifest["version"] == contract["version"]
        assert manifest["stage"] == contract["stage"]
        assert manifest["layer"] == contract["gate_layer"]
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert manifest["runtime_touch_mode"] == "none"
        assert manifest["launcher_touch_mode"] == "none"
        assert manifest["provider_touch_mode"] == "none"
        assert manifest["real_translation"] is False
        assert manifest["required_freezes"] == contract["required_freezes"]
        assert manifest["readiness_checks"] == contract["readiness_checks"]
        assert manifest["forbidden_side_effects"] == contract["forbidden_side_effects"]
        assert "te_v36_runtime_safe_hook_preflight_freeze_preserved" in manifest["guarantees"]

        bad_contract = {**contract, "runtime_touch_mode": "read"}
        assert builder.validate_contract(bad_contract)["valid"] is False

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_readiness_gate_contract_defaults_validation_and_description()
    test_runtime_readiness_gate_contract_manifest_and_safety()
    print("NTPE TE-v3.7 Stage-3.7.1 Runtime Readiness Gate Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

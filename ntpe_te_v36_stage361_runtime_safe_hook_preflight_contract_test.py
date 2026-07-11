from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v36_runtime_safe_hook_preflight_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_safe_hook_preflight_contract_defaults_validation_and_description() -> None:
    builder = RuntimeSafeHookPreflightContract()
    contract = builder.build_contract(metadata={"profile": "safe-preflight"})
    description = builder.describe_preflight()

    assert contract["version"] == "TE-v3.6"
    assert contract["stage"] == "3.6.1"
    assert contract["preflight_layer"] == "runtime_safe_adapter_hook_preflight"
    assert contract["default_mode"] == "disabled"
    assert contract["enabled_mode"] == "mock_only"
    assert contract["runtime_touch_mode"] == "none"
    assert contract["launcher_touch_mode"] == "none"
    assert contract["provider_touch_mode"] == "none"
    assert contract["real_translation"] is False
    assert set(contract["required_frozen_layers"]) == {
        "TE-v3.2 runtime_scheduler_adapter",
        "TE-v3.3 runtime_integration_planning",
        "TE-v3.4 runtime_optin_hook",
        "TE-v3.5 runtime_disabled_trial",
    }
    assert set(contract["required_prechecks"]) == {
        "RuntimeIntegrationFeatureFlag",
        "RuntimeOptInHookGuard",
        "RuntimeDisabledTrialGuard",
        "RuntimeDisabledTrialMockBridge",
    }
    assert set(contract["expected_preflight_inputs"]) == {"runtime_state", "resume_plan", "config", "env"}
    assert set(contract["expected_preflight_outputs"]) == {
        "preflight_status",
        "trial_status",
        "hook_status",
        "integration_status",
        "runtime_report",
        "export_outputs",
    }
    assert set(contract["forbidden_side_effects"]) == {
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "translation_runtime_flow",
        "real_translation",
    }
    assert builder.validate_contract(contract)["valid"] is True
    assert description["runtime_touch_mode"] == "none"
    assert description["launcher_touch_mode"] == "none"
    assert description["provider_touch_mode"] == "none"
    assert description["real_translation"] is False
    assert "TE-v3.5 runtime_disabled_trial" in description["required_frozen_layers"]


def test_runtime_safe_hook_preflight_contract_manifest_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeSafeHookPreflightContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        assert manifest["version"] == contract["version"]
        assert manifest["stage"] == contract["stage"]
        assert manifest["layer"] == contract["preflight_layer"]
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert manifest["runtime_touch_mode"] == "none"
        assert manifest["launcher_touch_mode"] == "none"
        assert manifest["provider_touch_mode"] == "none"
        assert manifest["real_translation"] is False
        assert manifest["required_frozen_layers"] == contract["required_frozen_layers"]
        assert manifest["required_prechecks"] == contract["required_prechecks"]
        assert manifest["forbidden_side_effects"] == contract["forbidden_side_effects"]
        assert "te_v35_runtime_disabled_trial_freeze_preserved" in manifest["guarantees"]

        bad_contract = {**contract, "enabled_mode": "real"}
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
    test_runtime_safe_hook_preflight_contract_defaults_validation_and_description()
    test_runtime_safe_hook_preflight_contract_manifest_and_safety()
    print("NTPE TE-v3.6 Stage-3.6.1 Runtime Safe Hook Preflight Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

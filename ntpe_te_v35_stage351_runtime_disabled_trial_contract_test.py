from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeDisabledTrialContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v35_runtime_disabled_trial_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_disabled_trial_contract_defaults_validation_and_description() -> None:
    builder = RuntimeDisabledTrialContract()
    contract = builder.build_contract(metadata={"profile": "disabled-trial"})
    description = builder.describe_trial()

    assert contract["version"] == "TE-v3.5"
    assert contract["stage"] == "3.5.1"
    assert contract["trial_layer"] == "runtime_adapter_hook_disabled_trial"
    assert contract["default_mode"] == "disabled"
    assert contract["enabled_mode"] == "mock_only"
    assert contract["runtime_touch_mode"] == "none"
    assert contract["launcher_touch_mode"] == "none"
    assert contract["provider_touch_mode"] == "none"
    assert contract["real_translation"] is False
    assert set(contract["required_prechecks"]) == {
        "RuntimeIntegrationFeatureFlag",
        "RuntimeOptInHookGuard",
        "RuntimeOptInHookMockBridge",
    }
    assert set(contract["expected_trial_inputs"]) == {"runtime_state", "resume_plan", "config", "env"}
    assert set(contract["expected_trial_outputs"]) == {
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


def test_runtime_disabled_trial_contract_manifest_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeDisabledTrialContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        assert manifest["version"] == contract["version"]
        assert manifest["stage"] == contract["stage"]
        assert manifest["layer"] == contract["trial_layer"]
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert manifest["runtime_touch_mode"] == "none"
        assert manifest["launcher_touch_mode"] == "none"
        assert manifest["provider_touch_mode"] == "none"
        assert manifest["real_translation"] is False
        assert manifest["required_prechecks"] == contract["required_prechecks"]
        assert manifest["forbidden_side_effects"] == contract["forbidden_side_effects"]
        assert "te_v34_runtime_optin_hook_freeze_preserved" in manifest["guarantees"]

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
    test_runtime_disabled_trial_contract_defaults_validation_and_description()
    test_runtime_disabled_trial_contract_manifest_and_safety()
    print("NTPE TE-v3.5 Stage-3.5.1 Runtime Disabled Trial Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

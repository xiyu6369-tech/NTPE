from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v34_runtime_optin_hook_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_optin_hook_contract_defaults_validation_and_description() -> None:
    builder = RuntimeOptInHookContract()
    contract = builder.build_contract(metadata={"profile": "planning"})
    description = builder.describe_hook()

    assert contract["version"] == "TE-v3.4"
    assert contract["stage"] == "3.4.1"
    assert contract["hook_layer"] == "runtime_optin_adapter_hook"
    assert contract["enabled_by_default"] is False
    assert contract["activation_mode"] == "explicit_opt_in_only"
    assert contract["execution_mode"] == "mock_only"
    assert contract["allowed_callers"] == ["translation_runtime"]
    assert set(contract["forbidden_side_effects"]) == {
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "real_translation",
    }
    assert set(contract["required_prechecks"]) == {
        "RuntimeIntegrationFeatureFlag",
        "RuntimeIntegrationDisabledGuard",
        "RuntimeIntegrationMockOrchestrator",
    }
    assert set(contract["expected_hook_inputs"]) == {"runtime_state", "resume_plan", "config", "env"}
    assert set(contract["expected_hook_outputs"]) == {
        "hook_status",
        "integration_status",
        "runtime_report",
        "export_outputs",
    }
    assert contract["metadata"]["disabled_by_default"] is True
    assert contract["metadata"]["real_translation"] is False
    assert builder.validate_contract(contract)["valid"] is True
    assert description["hook_layer"] == "runtime_optin_adapter_hook"
    assert description["activation_mode"] == "explicit_opt_in_only"
    assert description["execution_mode"] == "mock_only"


def test_runtime_optin_hook_contract_manifest_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeOptInHookContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        assert manifest["version"] == contract["version"]
        assert manifest["stage"] == contract["stage"]
        assert manifest["layer"] == contract["hook_layer"]
        assert manifest["enabled_by_default"] is False
        assert manifest["activation_mode"] == "explicit_opt_in_only"
        assert manifest["execution_mode"] == "mock_only"
        assert manifest["forbidden_side_effects"] == contract["forbidden_side_effects"]
        assert manifest["required_prechecks"] == contract["required_prechecks"]
        assert manifest["expected_hook_inputs"] == contract["expected_hook_inputs"]
        assert manifest["expected_hook_outputs"] == contract["expected_hook_outputs"]
        assert "te_v33_runtime_integration_freeze_preserved" in manifest["guarantees"]

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
    test_runtime_optin_hook_contract_defaults_validation_and_description()
    test_runtime_optin_hook_contract_manifest_and_safety()
    print("NTPE TE-v3.4 Stage-3.4.1 Runtime Opt-in Hook Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

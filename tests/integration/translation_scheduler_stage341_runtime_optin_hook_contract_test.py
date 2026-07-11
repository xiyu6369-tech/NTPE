from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookContract


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage341_runtime_optin_hook_contract_shape_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeOptInHookContract()
        contract = builder.build_contract()
        description = builder.describe_hook()

        assert builder.validate_contract(contract)["valid"] is True
        assert contract["enabled_by_default"] is False
        assert contract["activation_mode"] == "explicit_opt_in_only"
        assert contract["execution_mode"] == "mock_only"
        assert contract["allowed_callers"] == ["translation_runtime"]
        assert "provider_runtime" in contract["forbidden_side_effects"]
        assert "http_client" in contract["forbidden_side_effects"]
        assert "api_key" in contract["forbidden_side_effects"]
        assert "launcher_flow" in contract["forbidden_side_effects"]
        assert "real_translation" in contract["forbidden_side_effects"]
        assert "RuntimeIntegrationFeatureFlag" in contract["required_prechecks"]
        assert "RuntimeIntegrationDisabledGuard" in contract["required_prechecks"]
        assert "RuntimeIntegrationMockOrchestrator" in contract["required_prechecks"]
        assert description["summary"]

        bad_contract = {**contract, "execution_mode": "real"}
        assert builder.validate_contract(bad_contract)["valid"] is False

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

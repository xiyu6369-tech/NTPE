from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightContract


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage361_runtime_safe_hook_preflight_contract_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeSafeHookPreflightContract()
        contract = builder.build_contract()
        description = builder.describe_preflight()

        assert builder.validate_contract(contract)["valid"] is True
        assert contract["default_mode"] == "disabled"
        assert contract["enabled_mode"] == "mock_only"
        assert contract["runtime_touch_mode"] == "none"
        assert contract["launcher_touch_mode"] == "none"
        assert contract["provider_touch_mode"] == "none"
        assert contract["real_translation"] is False
        assert "TE-v3.2 runtime_scheduler_adapter" in contract["required_frozen_layers"]
        assert "TE-v3.3 runtime_integration_planning" in contract["required_frozen_layers"]
        assert "TE-v3.4 runtime_optin_hook" in contract["required_frozen_layers"]
        assert "TE-v3.5 runtime_disabled_trial" in contract["required_frozen_layers"]
        assert "RuntimeIntegrationFeatureFlag" in contract["required_prechecks"]
        assert "RuntimeOptInHookGuard" in contract["required_prechecks"]
        assert "RuntimeDisabledTrialGuard" in contract["required_prechecks"]
        assert "RuntimeDisabledTrialMockBridge" in contract["required_prechecks"]
        assert "translation_runtime_flow" in contract["forbidden_side_effects"]
        assert description["summary"]

        bad_contract = {**contract, "runtime_touch_mode": "read"}
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

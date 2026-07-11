from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationFeatureFlag


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage332_feature_flag_opt_in_rules_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        resolver = RuntimeIntegrationFeatureFlag()

        cases = [
            (resolver.resolve(), False, "default", "default_disabled"),
            (resolver.resolve(config={"runtime_scheduler_integration_enabled": True}), True, "config", "config_enabled"),
            (resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "1"}), True, "env", "env_enabled"),
            (
                resolver.resolve(
                    config={"runtime_scheduler_integration_enabled": False},
                    env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "1"},
                ),
                False,
                "config",
                "config_disabled",
            ),
            (resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "off"}), False, "env", "env_invalid_or_disabled"),
        ]

        for state, enabled, source, reason in cases:
            assert state["enabled"] is enabled
            assert state["source"] == source
            assert state["reason"] == reason
            assert resolver.is_enabled(state) is enabled
            assert resolver.validate_flag_state(state)["valid"] is True
            assert state["safety_boundaries"]["provider_runtime"] == "external"
            assert state["safety_boundaries"]["http_client"] == "forbidden"
            assert state["safety_boundaries"]["api_key"] == "forbidden"
            assert state["safety_boundaries"]["launcher_flow"] == "unchanged"
            assert state["safety_boundaries"]["translation_runtime_flow"] == "unchanged"

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

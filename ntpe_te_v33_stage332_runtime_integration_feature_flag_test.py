from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationFeatureFlag


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_feature_flag_resolution_rules() -> None:
    resolver = RuntimeIntegrationFeatureFlag()

    default_state = resolver.resolve()
    config_enabled = resolver.resolve(config={"runtime_scheduler_integration_enabled": True})
    env_enabled = resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "yes"})
    config_override = resolver.resolve(
        config={"runtime_scheduler_integration_enabled": False},
        env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"},
    )
    invalid_env = resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "maybe"})

    assert default_state["enabled"] is False
    assert default_state["source"] == "default"
    assert default_state["reason"] == "default_disabled"
    assert resolver.is_enabled(default_state) is False

    assert config_enabled["enabled"] is True
    assert config_enabled["source"] == "config"
    assert resolver.is_enabled(config_enabled) is True

    assert env_enabled["enabled"] is True
    assert env_enabled["source"] == "env"
    assert resolver.is_enabled(env_enabled) is True

    assert config_override["enabled"] is False
    assert config_override["source"] == "config"
    assert config_override["reason"] == "config_disabled"
    assert resolver.is_enabled(config_override) is False

    assert invalid_env["enabled"] is False
    assert invalid_env["source"] == "env"
    assert invalid_env["reason"] == "env_invalid_or_disabled"
    assert resolver.is_enabled(invalid_env) is False

    for state in (default_state, config_enabled, env_enabled, config_override, invalid_env):
        assert state["stage"] == "3.3.2"
        assert state["safety_boundaries"]["provider_runtime"] == "external"
        assert state["safety_boundaries"]["http_client"] == "forbidden"
        assert state["safety_boundaries"]["api_key"] == "forbidden"
        assert state["safety_boundaries"]["launcher_flow"] == "unchanged"
        assert state["safety_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert resolver.validate_flag_state(state)["valid"] is True


def test_feature_flag_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        resolver = RuntimeIntegrationFeatureFlag()
        state = resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "true"})

        assert state["enabled"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_feature_flag_resolution_rules()
    test_feature_flag_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.3 Stage-3.3.2 Runtime Integration Feature Flag PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

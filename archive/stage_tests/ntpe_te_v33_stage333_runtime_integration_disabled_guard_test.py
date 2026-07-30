from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationDisabledGuard, RuntimeIntegrationFeatureFlag


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_disabled_guard_blocks_and_allows_without_executing_jobs() -> None:
    flag = RuntimeIntegrationFeatureFlag()
    guard = RuntimeIntegrationDisabledGuard()
    request = {
        "runtime_id": "runtime-333",
        "type": "mock_integration",
        "source_text": "secret source text",
        "chunks": ["secret chunk 1", "secret chunk 2"],
    }

    default_result = guard.guard(flag.resolve(), request=request)
    enabled_result = guard.guard(flag.resolve(config={"runtime_scheduler_integration_enabled": True}), request=request)
    missing_result = guard.guard(None, request=request)

    assert default_result["allowed"] is False
    assert default_result["blocked"] is True
    assert default_result["reason"] == "runtime_integration_disabled"
    assert guard.is_blocked(default_result) is True
    assert default_result["request_summary"]["chunk_count"] == 2
    assert default_result["request_summary"]["has_source_text"] is True
    assert "secret source text" not in str(default_result)
    assert "secret chunk 1" not in str(default_result)

    assert enabled_result["allowed"] is True
    assert enabled_result["blocked"] is False
    assert enabled_result["reason"] == "runtime_integration_enabled"
    assert guard.is_blocked(enabled_result) is False

    assert missing_result["allowed"] is False
    assert missing_result["blocked"] is True
    assert missing_result["metadata"]["flag_source"] == "missing"

    for result in (default_result, enabled_result, missing_result):
        assert result["stage"] == "3.3.3"
        assert result["safety_boundaries"]["provider_runtime"] == "external"
        assert result["safety_boundaries"]["http_client"] == "forbidden"
        assert result["safety_boundaries"]["api_key"] == "forbidden"
        assert result["safety_boundaries"]["launcher_flow"] == "unchanged"
        assert result["safety_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert guard.validate_guard_result(result)["valid"] is True


def test_disabled_guard_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        guard = RuntimeIntegrationDisabledGuard()
        result = guard.guard(None, request={"source_text": "do not store me"})

        assert result["blocked"] is True
        assert "do not store me" not in str(result)
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
    test_disabled_guard_blocks_and_allows_without_executing_jobs()
    test_disabled_guard_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.3 Stage-3.3.3 Runtime Integration Disabled Guard PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

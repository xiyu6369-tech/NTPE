from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationDisabledGuard, RuntimeIntegrationFeatureFlag


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage333_disabled_guard_blocks_disabled_paths_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        resolver = RuntimeIntegrationFeatureFlag()
        guard = RuntimeIntegrationDisabledGuard()
        request = {
            "request_type": "integration_attempt",
            "runtime_id": "integration-333",
            "text": "sensitive text",
        }

        blocked = guard.guard(resolver.resolve(), request=request)
        allowed = guard.guard(resolver.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"}), request=request)
        missing = guard.guard(None, request=request)

        assert blocked["allowed"] is False
        assert blocked["blocked"] is True
        assert blocked["reason"] == "runtime_integration_disabled"
        assert guard.is_blocked(blocked) is True
        assert blocked["request_summary"]["runtime_id"] == "integration-333"
        assert blocked["request_summary"]["chunk_count"] == 1
        assert "sensitive text" not in str(blocked)

        assert allowed["allowed"] is True
        assert allowed["blocked"] is False
        assert guard.is_blocked(allowed) is False

        assert missing["blocked"] is True
        assert missing["metadata"]["flag_reason"] == "missing_flag_state"

        for result in (blocked, allowed, missing):
            assert guard.validate_guard_result(result)["valid"] is True
            assert result["safety_boundaries"]["provider_runtime"] == "external"
            assert result["safety_boundaries"]["http_client"] == "forbidden"
            assert result["safety_boundaries"]["api_key"] == "forbidden"
            assert result["safety_boundaries"]["launcher_flow"] == "unchanged"
            assert result["safety_boundaries"]["translation_runtime_flow"] == "unchanged"

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

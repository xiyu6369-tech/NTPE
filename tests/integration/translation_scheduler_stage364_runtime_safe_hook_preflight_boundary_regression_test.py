from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeSafeHookPreflightContract,
    RuntimeSafeHookPreflightGuard,
    RuntimeSafeHookPreflightMockBridge,
)


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration safe hook preflight boundary secret"


def test_stage364_safe_hook_preflight_boundary_regression_keeps_bridge_mock_only() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        assert RuntimeSafeHookPreflightContract is not None
        assert RuntimeSafeHookPreflightGuard is not None
        assert RuntimeSafeHookPreflightMockBridge is not None

        bridge = RuntimeSafeHookPreflightMockBridge()
        request = {
            "request_type": "safe_hook_preflight",
            "runtime_id": "integration-364",
            "source_text": SECRET_TEXT,
            "chunks": [SECRET_TEXT],
        }
        blocked = bridge.run(request=request)
        completed = bridge.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert blocked["status"] == "preflight_blocked"
        assert blocked["disabled_trial_result"] == {}
        assert blocked["runtime_report"] == {}
        assert blocked["export_outputs"] == {}

        assert completed["status"] == "preflight_mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["integration_status"]["real_translation"] is False
        assert completed["runtime_report"]["provider_runtime"] in {"not_connected", "external"}
        assert completed["preflight_guard_result"]["safety_boundaries"]["http_client"] in {"forbidden", "not_called"}
        assert completed["preflight_guard_result"]["safety_boundaries"]["api_key"] in {"forbidden", "not_used"}
        assert completed["preflight_guard_result"]["safety_boundaries"]["launcher_flow"] == "unchanged"
        assert completed["preflight_guard_result"]["safety_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert completed["export_outputs"]["merged_text"] == ""
        assert completed["export_outputs"]["chunk_results"] == []
        assert completed["export_outputs"]["failed_chunks"] == []

        for result in (blocked, completed):
            assert bridge.validate_result(result)["valid"] is True
            assert SECRET_TEXT not in str(result)

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

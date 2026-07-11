from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightMockBridge


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration safe preflight source"


def test_stage363_runtime_safe_hook_preflight_mock_bridge_boundaries() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeSafeHookPreflightMockBridge()
        request = {
            "request_type": "safe_hook_preflight",
            "runtime_id": "integration-363",
            "text": SECRET_TEXT,
            "chunks": [SECRET_TEXT],
        }

        blocked = bridge.run(request=request)
        assert blocked["status"] == "preflight_blocked"
        assert blocked["disabled_trial_result"] == {}
        assert blocked["runtime_report"] == {}
        assert blocked["export_outputs"] == {}
        assert bridge.validate_result(blocked)["valid"] is True

        completed = bridge.run(request=request, config={"runtime_scheduler_integration_enabled": True})
        assert completed["status"] == "preflight_mock_completed"
        assert completed["disabled_trial_result"]["status"] == "trial_mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["integration_status"]["real_translation"] is False
        assert completed["export_outputs"]["merged_text"] == ""
        assert completed["export_outputs"]["chunk_results"] == []
        assert bridge.validate_result(completed)["valid"] is True

        for result in (blocked, completed):
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

from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookMockBridge


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration hook bridge secret"


def test_stage343_hook_mock_bridge_blocks_and_runs_mock_only_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeOptInHookMockBridge()
        request = {"caller": "translation_runtime", "runtime_id": "integration-343", "source_text": SECRET_TEXT}

        blocked = bridge.run(request=request)
        completed = bridge.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert blocked["status"] == "hook_blocked"
        assert blocked["orchestrator_result"] == {}
        assert blocked["runtime_report"] == {}
        assert blocked["export_outputs"] == {}
        assert blocked["hook_guard_result"]["request_summary"]["chunk_count"] == 1

        assert completed["status"] == "hook_mock_completed"
        assert completed["orchestrator_result"]["status"] == "mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["integration_status"]["real_translation"] is False
        assert completed["export_outputs"]["merged_text"] == ""
        assert completed["export_outputs"]["chunk_results"] == []

        for result in (blocked, completed):
            assert SECRET_TEXT not in str(result)
            assert bridge.validate_result(result)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

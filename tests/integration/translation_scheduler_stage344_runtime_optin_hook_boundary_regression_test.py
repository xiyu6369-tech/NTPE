from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookContract, RuntimeOptInHookGuard, RuntimeOptInHookMockBridge


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration hook boundary secret"


def test_stage344_hook_boundary_regression_keeps_bridge_mock_only() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        assert RuntimeOptInHookContract is not None
        assert RuntimeOptInHookGuard is not None
        assert RuntimeOptInHookMockBridge is not None

        bridge = RuntimeOptInHookMockBridge()
        request = {"caller": "translation_runtime", "runtime_id": "integration-344", "source_text": SECRET_TEXT}
        blocked = bridge.run(request=request)
        completed = bridge.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert blocked["status"] == "hook_blocked"
        assert blocked["orchestrator_result"] == {}
        assert completed["status"] == "hook_mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["integration_status"]["real_translation"] is False
        assert completed["runtime_report"]["provider_runtime"] in {"not_connected", "external"}
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

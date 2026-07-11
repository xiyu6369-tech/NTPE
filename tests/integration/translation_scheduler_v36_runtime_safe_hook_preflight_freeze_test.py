from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_SAFE_HOOK_PREFLIGHT_RELEASE_ID,
    RUNTIME_SAFE_HOOK_PREFLIGHT_STAGES,
    RUNTIME_SAFE_HOOK_PREFLIGHT_STATUS,
    RuntimeSafeHookPreflightContract,
    RuntimeSafeHookPreflightGuard,
    RuntimeSafeHookPreflightMockBridge,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v36_runtime_safe_hook_preflight_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration safe hook preflight freeze secret"


def test_v36_runtime_safe_hook_preflight_freeze_manifest_and_boundaries() -> None:
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
        assert RUNTIME_SAFE_HOOK_PREFLIGHT_STATUS == "frozen"
        assert RUNTIME_SAFE_HOOK_PREFLIGHT_STAGES == ("3.6.1", "3.6.2", "3.6.3", "3.6.4")

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        bridge = RuntimeSafeHookPreflightMockBridge()
        request = {"request_type": "safe_hook_preflight", "runtime_id": "integration-freeze-365", "text": SECRET_TEXT}
        blocked = bridge.run(request=request)
        completed = bridge.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert manifest["release_id"] == RUNTIME_SAFE_HOOK_PREFLIGHT_RELEASE_ID
        assert manifest["layer"] == "runtime_safe_hook_preflight"
        assert manifest["frozen"] is True
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert manifest["runtime_touch_mode"] == "none"
        assert manifest["launcher_touch_mode"] == "none"
        assert manifest["provider_touch_mode"] == "none"
        assert len(manifest["stages"]) == 4
        assert blocked["status"] == "preflight_blocked"
        assert blocked["disabled_trial_result"] == {}
        assert completed["status"] == "preflight_mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["integration_status"]["real_translation"] is False
        assert completed["runtime_report"]["provider_runtime"] == "not_connected"
        assert completed["export_outputs"]["merged_text"] == ""
        assert completed["export_outputs"]["chunk_results"] == []
        assert SECRET_TEXT not in str(blocked)
        assert SECRET_TEXT not in str(completed)
        assert bridge.validate_result(blocked)["valid"] is True
        assert bridge.validate_result(completed)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

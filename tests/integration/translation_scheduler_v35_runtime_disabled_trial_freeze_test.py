from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_DISABLED_TRIAL_RELEASE_ID,
    RUNTIME_DISABLED_TRIAL_STAGES,
    RUNTIME_DISABLED_TRIAL_STATUS,
    RuntimeDisabledTrialContract,
    RuntimeDisabledTrialGuard,
    RuntimeDisabledTrialMockBridge,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v35_runtime_disabled_trial_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration disabled trial freeze secret"


def test_v35_runtime_disabled_trial_freeze_manifest_and_boundaries() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        assert RuntimeDisabledTrialContract is not None
        assert RuntimeDisabledTrialGuard is not None
        assert RuntimeDisabledTrialMockBridge is not None
        assert RUNTIME_DISABLED_TRIAL_STATUS == "frozen"
        assert RUNTIME_DISABLED_TRIAL_STAGES == ("3.5.1", "3.5.2", "3.5.3", "3.5.4")

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        bridge = RuntimeDisabledTrialMockBridge()
        request = {"request_type": "disabled_trial", "runtime_id": "integration-freeze-355", "text": SECRET_TEXT}
        blocked = bridge.run(request=request)
        completed = bridge.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert manifest["release_id"] == RUNTIME_DISABLED_TRIAL_RELEASE_ID
        assert manifest["layer"] == "runtime_disabled_trial"
        assert manifest["frozen"] is True
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert manifest["runtime_touch_mode"] == "none"
        assert manifest["launcher_touch_mode"] == "none"
        assert manifest["provider_touch_mode"] == "none"
        assert len(manifest["stages"]) == 4
        assert blocked["status"] == "trial_blocked"
        assert blocked["hook_bridge_result"] == {}
        assert completed["status"] == "trial_mock_completed"
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

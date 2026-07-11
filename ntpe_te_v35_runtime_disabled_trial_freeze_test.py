from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_DISABLED_TRIAL_RELEASE_ID,
    RUNTIME_DISABLED_TRIAL_STAGES,
    RUNTIME_DISABLED_TRIAL_STATUS,
    RUNTIME_DISABLED_TRIAL_VERSION,
    RuntimeDisabledTrialContract,
    RuntimeDisabledTrialGuard,
    RuntimeDisabledTrialMockBridge,
)


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v35_runtime_disabled_trial_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "disabled trial freeze secret"


def test_runtime_disabled_trial_freeze_imports_and_metadata() -> None:
    module = importlib.import_module("core.translation_scheduler")

    assert RuntimeDisabledTrialContract is not None
    assert RuntimeDisabledTrialGuard is not None
    assert RuntimeDisabledTrialMockBridge is not None
    assert module.RUNTIME_DISABLED_TRIAL_VERSION == "TE-v3.5"
    assert RUNTIME_DISABLED_TRIAL_VERSION == "TE-v3.5"
    assert RUNTIME_DISABLED_TRIAL_RELEASE_ID == "TE-v3.5-runtime-disabled-trial-freeze"
    assert RUNTIME_DISABLED_TRIAL_STATUS == "frozen"
    assert RUNTIME_DISABLED_TRIAL_STAGES == ("3.5.1", "3.5.2", "3.5.3", "3.5.4")


def test_runtime_disabled_trial_freeze_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == "TE-v3.5"
    assert manifest["release_id"] == RUNTIME_DISABLED_TRIAL_RELEASE_ID
    assert manifest["layer"] == "runtime_disabled_trial"
    assert manifest["frozen"] is True
    assert [stage["stage"] for stage in manifest["stages"]] == ["3.5.1", "3.5.2", "3.5.3", "3.5.4"]
    assert manifest["default_mode"] == "disabled"
    assert manifest["enabled_mode"] == "mock_only"
    assert manifest["runtime_touch_mode"] == "none"
    assert manifest["launcher_touch_mode"] == "none"
    assert manifest["provider_touch_mode"] == "none"
    assert "disabled_by_default" in manifest["guarantees"]
    assert "enabled_mode_mock_only" in manifest["guarantees"]
    assert "request_summary_does_not_store_source_text" in manifest["guarantees"]
    assert "te_v34_runtime_optin_hook_freeze_preserved" in manifest["guarantees"]
    assert "python ntpe_validate.py" in manifest["validation_commands"]
    assert manifest["next_stage"] == "TE-v3.6 Runtime Safe Adapter Hook Preflight"


def test_runtime_disabled_trial_freeze_blocked_and_mock_only_paths() -> None:
    bridge = RuntimeDisabledTrialMockBridge()
    request = {
        "request_type": "disabled_trial",
        "runtime_id": "freeze-355",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    blocked = bridge.run(request=request)
    completed = bridge.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "trial_blocked"
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}
    assert blocked["hook_bridge_result"] == {}

    assert completed["status"] == "trial_mock_completed"
    assert completed["hook_bridge_result"]["status"] == "hook_mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["provider_runtime"] == "not_connected"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []

    for result in (blocked, completed):
        assert bridge.validate_result(result)["valid"] is True
        assert SECRET_TEXT not in str(result)


def test_runtime_disabled_trial_freeze_no_runtime_provider_http_api_key_or_launcher_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        test_runtime_disabled_trial_freeze_blocked_and_mock_only_paths()

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_disabled_trial_freeze_imports_and_metadata()
    test_runtime_disabled_trial_freeze_manifest()
    test_runtime_disabled_trial_freeze_blocked_and_mock_only_paths()
    test_runtime_disabled_trial_freeze_no_runtime_provider_http_api_key_or_launcher_side_effects()
    print("NTPE TE-v3.5 Runtime Disabled Trial Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

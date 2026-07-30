from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_SAFE_HOOK_PREFLIGHT_RELEASE_ID,
    RUNTIME_SAFE_HOOK_PREFLIGHT_STAGES,
    RUNTIME_SAFE_HOOK_PREFLIGHT_STATUS,
    RUNTIME_SAFE_HOOK_PREFLIGHT_VERSION,
    RuntimeSafeHookPreflightContract,
    RuntimeSafeHookPreflightGuard,
    RuntimeSafeHookPreflightMockBridge,
)


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v36_runtime_safe_hook_preflight_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "safe hook preflight freeze secret"


def test_runtime_safe_hook_preflight_freeze_imports_and_metadata() -> None:
    module = importlib.import_module("core.translation_scheduler")

    assert RuntimeSafeHookPreflightContract is not None
    assert RuntimeSafeHookPreflightGuard is not None
    assert RuntimeSafeHookPreflightMockBridge is not None
    assert module.RUNTIME_SAFE_HOOK_PREFLIGHT_VERSION == "TE-v3.6"
    assert RUNTIME_SAFE_HOOK_PREFLIGHT_VERSION == "TE-v3.6"
    assert RUNTIME_SAFE_HOOK_PREFLIGHT_RELEASE_ID == "TE-v3.6-runtime-safe-hook-preflight-freeze"
    assert RUNTIME_SAFE_HOOK_PREFLIGHT_STATUS == "frozen"
    assert RUNTIME_SAFE_HOOK_PREFLIGHT_STAGES == ("3.6.1", "3.6.2", "3.6.3", "3.6.4")


def test_runtime_safe_hook_preflight_freeze_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == "TE-v3.6"
    assert manifest["release_id"] == RUNTIME_SAFE_HOOK_PREFLIGHT_RELEASE_ID
    assert manifest["layer"] == "runtime_safe_hook_preflight"
    assert manifest["frozen"] is True
    assert [stage["stage"] for stage in manifest["stages"]] == ["3.6.1", "3.6.2", "3.6.3", "3.6.4"]
    assert manifest["default_mode"] == "disabled"
    assert manifest["enabled_mode"] == "mock_only"
    assert manifest["runtime_touch_mode"] == "none"
    assert manifest["launcher_touch_mode"] == "none"
    assert manifest["provider_touch_mode"] == "none"
    assert "disabled_by_default" in manifest["guarantees"]
    assert "enabled_mode_mock_only" in manifest["guarantees"]
    assert "request_summary_does_not_store_source_text" in manifest["guarantees"]
    assert "te_v35_runtime_disabled_trial_freeze_preserved" in manifest["guarantees"]
    assert "python ntpe_validate.py" in manifest["validation_commands"]
    assert manifest["next_stage"] == "TE-v3.7 Runtime Readiness Gate"


def test_runtime_safe_hook_preflight_freeze_blocked_and_mock_only_paths() -> None:
    bridge = RuntimeSafeHookPreflightMockBridge()
    request = {
        "request_type": "safe_hook_preflight",
        "runtime_id": "freeze-365",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    blocked = bridge.run(request=request)
    completed = bridge.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "preflight_blocked"
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}
    assert blocked["disabled_trial_result"] == {}

    assert completed["status"] == "preflight_mock_completed"
    assert completed["disabled_trial_result"]["status"] == "trial_mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["provider_runtime"] == "not_connected"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []

    for result in (blocked, completed):
        assert bridge.validate_result(result)["valid"] is True
        assert SECRET_TEXT not in str(result)


def test_runtime_safe_hook_preflight_freeze_no_runtime_provider_http_api_key_or_launcher_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        test_runtime_safe_hook_preflight_freeze_blocked_and_mock_only_paths()

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
    test_runtime_safe_hook_preflight_freeze_imports_and_metadata()
    test_runtime_safe_hook_preflight_freeze_manifest()
    test_runtime_safe_hook_preflight_freeze_blocked_and_mock_only_paths()
    test_runtime_safe_hook_preflight_freeze_no_runtime_provider_http_api_key_or_launcher_side_effects()
    print("NTPE TE-v3.6 Runtime Safe Hook Preflight Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeSafeHookPreflightContract,
    RuntimeSafeHookPreflightGuard,
    RuntimeSafeHookPreflightMockBridge,
)


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v36_runtime_safe_hook_preflight_boundary_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "safe hook preflight boundary secret text"


def test_safe_hook_preflight_boundary_imports_and_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert RuntimeSafeHookPreflightContract is not None
    assert RuntimeSafeHookPreflightGuard is not None
    assert RuntimeSafeHookPreflightMockBridge is not None
    assert manifest["version"] == "TE-v3.6"
    assert manifest["stage"] == "3.6.4"
    assert manifest["layer"] == "runtime_safe_hook_preflight_boundary"
    assert "RuntimeSafeHookPreflightMockBridge" in manifest["components"]
    assert "request_summary_does_not_store_source_text" in manifest["guarantees"]
    assert "te_v35_runtime_disabled_trial_freeze_preserved" in manifest["guarantees"]


def test_safe_hook_preflight_boundary_blocked_and_mock_paths() -> None:
    bridge = RuntimeSafeHookPreflightMockBridge()
    request = {
        "request_type": "safe_hook_preflight",
        "runtime_id": "boundary-364",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    blocked = bridge.run(request=request)
    completed = bridge.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "preflight_blocked"
    assert blocked["disabled_trial_result"] == {}
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}

    assert completed["status"] == "preflight_mock_completed"
    assert completed["disabled_trial_result"]["status"] == "trial_mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["provider_runtime"] in {"not_connected", "external"}
    assert completed["preflight_guard_result"]["safety_boundaries"]["provider_runtime"] == "forbidden"
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


def test_safe_hook_preflight_boundary_no_runtime_provider_http_api_key_or_launcher_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeSafeHookPreflightMockBridge()
        result = bridge.run(
            request={"request_type": "safe_hook_preflight", "runtime_id": "boundary-364", "text": SECRET_TEXT},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "preflight_mock_completed"
        assert result["integration_status"]["executed"] is False
        assert result["integration_status"]["real_translation"] is False
        assert result["export_outputs"]["merged_text"] == ""
        assert result["export_outputs"]["chunk_results"] == []
        assert SECRET_TEXT not in str(result)
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
    test_safe_hook_preflight_boundary_imports_and_manifest()
    test_safe_hook_preflight_boundary_blocked_and_mock_paths()
    test_safe_hook_preflight_boundary_no_runtime_provider_http_api_key_or_launcher_side_effects()
    print("NTPE TE-v3.6 Stage-3.6.4 Runtime Safe Hook Preflight Boundary Regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

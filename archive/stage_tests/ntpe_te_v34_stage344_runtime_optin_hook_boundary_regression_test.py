from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookContract, RuntimeOptInHookGuard, RuntimeOptInHookMockBridge


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v34_runtime_optin_hook_boundary_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "hook boundary secret text"


def test_hook_boundary_imports_and_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert RuntimeOptInHookContract is not None
    assert RuntimeOptInHookGuard is not None
    assert RuntimeOptInHookMockBridge is not None
    assert manifest["version"] == "TE-v3.4"
    assert manifest["stage"] == "3.4.4"
    assert manifest["layer"] == "runtime_optin_hook_boundary"
    assert "RuntimeOptInHookMockBridge" in manifest["components"]
    assert "request_summary_does_not_store_source_text" in manifest["guarantees"]


def test_hook_boundary_blocked_and_mock_paths() -> None:
    bridge = RuntimeOptInHookMockBridge()
    request = {
        "caller": "translation_runtime",
        "runtime_id": "boundary-344",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    blocked = bridge.run(request=request)
    completed = bridge.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "hook_blocked"
    assert blocked["orchestrator_result"] == {}
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}

    assert completed["status"] == "hook_mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["provider_runtime"] in {"not_connected", "external"}
    assert completed["orchestrator_result"]["contract"]["required_boundaries"]["http_client"] in {"forbidden", "not_called"}
    assert completed["orchestrator_result"]["contract"]["required_boundaries"]["api_key"] in {"forbidden", "not_used"}
    assert completed["orchestrator_result"]["contract"]["required_boundaries"]["launcher_flow"] == "unchanged"
    assert completed["orchestrator_result"]["contract"]["required_boundaries"]["translation_runtime_flow"] == "unchanged"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []

    for result in (blocked, completed):
        assert bridge.validate_result(result)["valid"] is True
        assert SECRET_TEXT not in str(result)


def test_hook_boundary_no_runtime_provider_http_api_key_or_launcher_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeOptInHookMockBridge()
        result = bridge.run(
            request={"caller": "translation_runtime", "text": SECRET_TEXT},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "hook_mock_completed"
        assert result["integration_status"]["executed"] is False
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
    test_hook_boundary_imports_and_manifest()
    test_hook_boundary_blocked_and_mock_paths()
    test_hook_boundary_no_runtime_provider_http_api_key_or_launcher_side_effects()
    print("NTPE TE-v3.4 Stage-3.4.4 Runtime Opt-in Hook Boundary Regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

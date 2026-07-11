from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_INTEGRATION_RELEASE_ID,
    RUNTIME_INTEGRATION_STAGES,
    RUNTIME_INTEGRATION_STATUS,
    RUNTIME_INTEGRATION_VERSION,
    RuntimeIntegrationContract,
    RuntimeIntegrationDisabledGuard,
    RuntimeIntegrationFeatureFlag,
    RuntimeIntegrationMockOrchestrator,
)


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "freeze secret text must not be stored"


def test_runtime_integration_freeze_imports_and_metadata() -> None:
    module = importlib.import_module("core.translation_scheduler")

    assert RuntimeIntegrationContract is not None
    assert RuntimeIntegrationFeatureFlag is not None
    assert RuntimeIntegrationDisabledGuard is not None
    assert RuntimeIntegrationMockOrchestrator is not None
    assert module.RUNTIME_INTEGRATION_VERSION == "TE-v3.3"
    assert RUNTIME_INTEGRATION_VERSION == "TE-v3.3"
    assert RUNTIME_INTEGRATION_RELEASE_ID == "TE-v3.3-runtime-integration-freeze"
    assert RUNTIME_INTEGRATION_STATUS == "frozen"
    assert RUNTIME_INTEGRATION_STAGES == ("3.3.1", "3.3.2", "3.3.3", "3.3.4", "3.3.5")


def test_runtime_integration_freeze_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == "TE-v3.3"
    assert manifest["release_id"] == RUNTIME_INTEGRATION_RELEASE_ID
    assert manifest["layer"] == "runtime_integration_planning"
    assert manifest["frozen"] is True
    assert [stage["stage"] for stage in manifest["stages"]] == ["3.3.1", "3.3.2", "3.3.3", "3.3.4", "3.3.5"]
    assert manifest["default_mode"] == "disabled"
    assert manifest["enabled_mode"] == "mock_only"
    assert "disabled_by_default" in manifest["guarantees"]
    assert "enabled_mode_mock_only" in manifest["guarantees"]
    assert "no_real_translation_execution_path" in manifest["guarantees"]
    assert "python ntpe_validate.py" in manifest["validation_commands"]
    assert manifest["next_stage"] == "TE-v3.4 Runtime Opt-in Adapter Hook Planning"


def test_runtime_integration_freeze_blocked_and_mock_only_paths() -> None:
    orchestrator = RuntimeIntegrationMockOrchestrator()
    request = {
        "runtime_id": "freeze-336",
        "request_type": "freeze",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    blocked = orchestrator.run(request=request)
    completed = orchestrator.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "blocked"
    assert blocked["allowed"] is False
    assert blocked["blocked"] is True
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}
    assert blocked["integration_status"]["mode"] == "blocked"

    assert completed["status"] == "mock_completed"
    assert completed["allowed"] is True
    assert completed["blocked"] is False
    assert completed["runtime_report"]["mode"] == "mock"
    assert completed["runtime_report"]["provider_runtime"] == "not_connected"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []

    for result in (blocked, completed):
        assert orchestrator.validate_result(result)["valid"] is True
        boundaries = result["guard_result"]["safety_boundaries"]
        assert boundaries["provider_runtime"] == "external"
        assert boundaries["http_client"] == "forbidden"
        assert boundaries["api_key"] == "forbidden"
        assert boundaries["launcher_flow"] == "unchanged"
        assert boundaries["translation_runtime_flow"] == "unchanged"
        assert SECRET_TEXT not in str(result)


def test_runtime_integration_freeze_no_provider_http_api_key_launcher_or_runtime_flow() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        test_runtime_integration_freeze_blocked_and_mock_only_paths()

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
    test_runtime_integration_freeze_imports_and_metadata()
    test_runtime_integration_freeze_manifest()
    test_runtime_integration_freeze_blocked_and_mock_only_paths()
    test_runtime_integration_freeze_no_provider_http_api_key_launcher_or_runtime_flow()
    print("NTPE TE-v3.3 Runtime Integration Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

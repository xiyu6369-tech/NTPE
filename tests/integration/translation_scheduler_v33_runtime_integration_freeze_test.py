from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_INTEGRATION_RELEASE_ID,
    RUNTIME_INTEGRATION_STAGES,
    RUNTIME_INTEGRATION_STATUS,
    RuntimeIntegrationContract,
    RuntimeIntegrationDisabledGuard,
    RuntimeIntegrationFeatureFlag,
    RuntimeIntegrationMockOrchestrator,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration freeze secret"


def test_v33_runtime_integration_freeze_manifest_and_boundaries() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        assert RuntimeIntegrationContract is not None
        assert RuntimeIntegrationFeatureFlag is not None
        assert RuntimeIntegrationDisabledGuard is not None
        assert RuntimeIntegrationMockOrchestrator is not None
        assert RUNTIME_INTEGRATION_STATUS == "frozen"
        assert RUNTIME_INTEGRATION_STAGES == ("3.3.1", "3.3.2", "3.3.3", "3.3.4", "3.3.5")

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        orchestrator = RuntimeIntegrationMockOrchestrator()
        request = {"runtime_id": "integration-freeze-336", "text": SECRET_TEXT}
        blocked = orchestrator.run(request=request)
        completed = orchestrator.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert manifest["release_id"] == RUNTIME_INTEGRATION_RELEASE_ID
        assert manifest["layer"] == "runtime_integration_planning"
        assert manifest["frozen"] is True
        assert manifest["default_mode"] == "disabled"
        assert manifest["enabled_mode"] == "mock_only"
        assert len(manifest["stages"]) == 5
        assert blocked["status"] == "blocked"
        assert blocked["runtime_report"] == {}
        assert completed["status"] == "mock_completed"
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["executed"] is False
        assert completed["runtime_report"]["provider_runtime"] == "not_connected"
        assert completed["export_outputs"]["merged_text"] == ""
        assert completed["export_outputs"]["chunk_results"] == []
        assert SECRET_TEXT not in str(blocked)
        assert SECRET_TEXT not in str(completed)
        assert orchestrator.validate_result(blocked)["valid"] is True
        assert orchestrator.validate_result(completed)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

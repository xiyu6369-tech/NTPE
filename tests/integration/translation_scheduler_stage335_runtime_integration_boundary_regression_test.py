from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeIntegrationContract,
    RuntimeIntegrationDisabledGuard,
    RuntimeIntegrationFeatureFlag,
    RuntimeIntegrationMockOrchestrator,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_boundary_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration secret text"


def test_stage335_boundary_regression_keeps_runtime_integration_mock_only() -> None:
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

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        orchestrator = RuntimeIntegrationMockOrchestrator()
        request = {"runtime_id": "integration-boundary-335", "source_text": SECRET_TEXT, "chunks": [SECRET_TEXT]}
        blocked = orchestrator.run(request=request)
        completed = orchestrator.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert manifest["stage"] == "3.3.5"
        assert blocked["status"] == "blocked"
        assert blocked["runtime_report"] == {}
        assert blocked["export_outputs"] == {}
        assert completed["status"] == "mock_completed"
        assert completed["runtime_report"]["provider_runtime"] in {"not_connected", "external"}
        assert completed["contract"]["required_boundaries"]["http_client"] in {"forbidden", "not_called"}
        assert completed["contract"]["required_boundaries"]["api_key"] in {"forbidden", "not_used"}
        assert completed["contract"]["required_boundaries"]["launcher_flow"] == "unchanged"
        assert completed["contract"]["required_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert completed["integration_status"]["executed"] is False
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

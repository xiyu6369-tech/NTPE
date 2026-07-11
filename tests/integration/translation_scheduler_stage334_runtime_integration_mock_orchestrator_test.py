from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationMockOrchestrator


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage334_mock_orchestrator_blocks_by_default_and_completes_mock_only() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        orchestrator = RuntimeIntegrationMockOrchestrator()
        request = {
            "runtime_id": "integration-334",
            "type": "mock",
            "text": "sensitive text",
        }

        blocked = orchestrator.run(request=request)
        completed = orchestrator.run(request=request, env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"})

        assert blocked["status"] == "blocked"
        assert blocked["blocked"] is True
        assert blocked["runtime_report"] == {}
        assert blocked["export_outputs"] == {}
        assert blocked["integration_status"]["mode"] == "blocked"
        assert "sensitive text" not in str(blocked)
        assert orchestrator.validate_result(blocked)["valid"] is True

        assert completed["status"] == "mock_completed"
        assert completed["allowed"] is True
        assert completed["runtime_report"]["mode"] == "mock"
        assert completed["runtime_report"]["jobs_total"] == 1
        assert completed["export_outputs"]["manifest"]["mock"] is True
        assert completed["export_outputs"]["chunk_results"] == []
        assert completed["integration_status"]["mode"] == "mock"
        assert completed["integration_status"]["provider_runtime"] == "not_connected"
        assert "sensitive text" not in str(completed)
        assert orchestrator.validate_result(completed)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

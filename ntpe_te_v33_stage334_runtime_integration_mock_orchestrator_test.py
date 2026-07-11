from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationMockOrchestrator


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_mock_orchestrator_blocked_and_enabled_paths() -> None:
    orchestrator = RuntimeIntegrationMockOrchestrator()
    request = {
        "runtime_id": "runtime-334",
        "request_type": "mock_orchestration",
        "source_text": "private source text",
        "chunks": ["private chunk 1", "private chunk 2"],
    }

    blocked = orchestrator.run(request=request)
    completed = orchestrator.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "blocked"
    assert blocked["allowed"] is False
    assert blocked["blocked"] is True
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}
    assert blocked["integration_status"]["mode"] == "blocked"
    assert blocked["guard_result"]["request_summary"]["chunk_count"] == 2
    assert "private source text" not in str(blocked)
    assert "private chunk 1" not in str(blocked)
    assert orchestrator.validate_result(blocked)["valid"] is True

    assert completed["status"] == "mock_completed"
    assert completed["allowed"] is True
    assert completed["blocked"] is False
    assert completed["runtime_report"]["mode"] == "mock"
    assert completed["runtime_report"]["jobs_total"] == 2
    assert completed["runtime_report"]["provider_runtime"] == "not_connected"
    assert completed["export_outputs"]["mode"] == "mock"
    assert completed["export_outputs"]["chunk_results"] == []
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert "private source text" not in str(completed)
    assert "private chunk 2" not in str(completed)
    assert orchestrator.validate_result(completed)["valid"] is True


def test_mock_orchestrator_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        orchestrator = RuntimeIntegrationMockOrchestrator()
        result = orchestrator.run(
            request={"source_text": "do not store me"},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "mock_completed"
        assert "do not store me" not in str(result)
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_mock_orchestrator_blocked_and_enabled_paths()
    test_mock_orchestrator_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.3 Stage-3.3.4 Runtime Integration Mock Orchestrator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_boundary_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_SOURCE = "secret source text must not be stored"
SECRET_CHUNK = "secret chunk text must not be stored"


def test_boundary_regression_imports_and_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert RuntimeIntegrationContract is not None
    assert RuntimeIntegrationFeatureFlag is not None
    assert RuntimeIntegrationDisabledGuard is not None
    assert RuntimeIntegrationMockOrchestrator is not None
    assert manifest["version"] == "TE-v3.3"
    assert manifest["stage"] == "3.3.5"
    assert manifest["layer"] == "runtime_scheduler_integration_boundary"
    assert "RuntimeIntegrationMockOrchestrator" in manifest["components"]
    assert manifest["forbidden_boundaries"]["provider_runtime"] == ["not_connected", "external"]
    assert "no_real_translation_output" in manifest["guarantees"]


def test_boundary_regression_blocked_and_mock_paths() -> None:
    orchestrator = RuntimeIntegrationMockOrchestrator()
    request = {
        "runtime_id": "boundary-335",
        "request_type": "boundary_regression",
        "source_text": SECRET_SOURCE,
        "chunks": [SECRET_CHUNK],
    }

    blocked = orchestrator.run(request=request)
    completed = orchestrator.run(request=request, config={"runtime_scheduler_integration_enabled": True})

    assert blocked["status"] == "blocked"
    assert blocked["runtime_report"] == {}
    assert blocked["export_outputs"] == {}
    assert blocked["guard_result"]["request_summary"]["chunk_count"] == 1

    assert completed["status"] == "mock_completed"
    assert completed["runtime_report"]["provider_runtime"] == "not_connected"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["export_outputs"]["mode"] == "mock"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []
    assert completed["export_outputs"]["failed_chunks"] == []

    for result in (blocked, completed):
        assert orchestrator.validate_result(result)["valid"] is True
        boundaries = result["guard_result"]["safety_boundaries"]
        assert boundaries["provider_runtime"] == "external"
        assert boundaries["http_client"] == "forbidden"
        assert boundaries["api_key"] == "forbidden"
        assert boundaries["launcher_flow"] == "unchanged"
        assert boundaries["translation_runtime_flow"] == "unchanged"
        assert SECRET_SOURCE not in str(result)
        assert SECRET_CHUNK not in str(result)


def test_boundary_regression_no_provider_http_api_key_launcher_or_runtime_flow() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        orchestrator = RuntimeIntegrationMockOrchestrator()
        result = orchestrator.run(
            request={"runtime_id": "boundary-335", "text": SECRET_SOURCE},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "mock_completed"
        assert result["runtime_report"]["jobs_total"] == 1
        assert result["integration_status"]["provider_runtime"] == "not_connected"
        assert result["contract"]["required_boundaries"]["http_client"] == "forbidden"
        assert result["contract"]["required_boundaries"]["api_key"] == "forbidden"
        assert result["contract"]["required_boundaries"]["launcher_flow"] == "unchanged"
        assert result["contract"]["required_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert SECRET_SOURCE not in str(result)
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
    test_boundary_regression_imports_and_manifest()
    test_boundary_regression_blocked_and_mock_paths()
    test_boundary_regression_no_provider_http_api_key_launcher_or_runtime_flow()
    print("NTPE TE-v3.3 Stage-3.3.5 Runtime Integration Boundary Regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

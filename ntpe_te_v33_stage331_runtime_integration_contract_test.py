from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_integration_contract_defaults_and_validation() -> None:
    contract_builder = RuntimeIntegrationContract()
    contract = contract_builder.build_contract(metadata={"profile": "planning"})

    assert contract["version"] == "TE-v3.3"
    assert contract["stage"] == "3.3.1"
    assert contract["integration_layer"] == "runtime_scheduler_integration"
    assert contract["enabled"] is False
    assert contract["default_mode"] == "disabled"
    assert contract_builder.is_enabled(contract) is False
    assert contract["required_boundaries"]["provider_runtime"] == "external"
    assert contract["required_boundaries"]["http_client"] == "forbidden"
    assert contract["required_boundaries"]["api_key"] == "forbidden"
    assert contract["required_boundaries"]["launcher_flow"] == "unchanged"
    assert contract["required_boundaries"]["translation_runtime_flow"] == "unchanged"
    assert contract["required_inputs"] == ["runtime_state", "scheduler_snapshot", "resume_plan"]
    assert contract["expected_outputs"] == ["runtime_report", "export_outputs", "integration_status"]
    assert contract["metadata"]["disabled_by_default"] is True
    assert contract_builder.validate_contract(contract)["valid"] is True


def test_runtime_integration_contract_manifest_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        contract_builder = RuntimeIntegrationContract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        contract = contract_builder.build_contract()

        assert manifest["version"] == "TE-v3.3"
        assert manifest["stage"] == "3.3.1"
        assert manifest["enabled"] is False
        assert manifest["default_mode"] == "disabled"
        assert manifest["required_boundaries"] == contract["required_boundaries"]
        assert manifest["required_inputs"] == contract["required_inputs"]
        assert manifest["expected_outputs"] == contract["expected_outputs"]
        assert "disabled_by_default" in manifest["guarantees"]
        assert "te_v32_runtime_scheduler_freeze_preserved" in manifest["guarantees"]

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
    test_runtime_integration_contract_defaults_and_validation()
    test_runtime_integration_contract_manifest_and_safety()
    print("NTPE TE-v3.3 Stage-3.3.1 Runtime Integration Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationContract


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v33_runtime_integration_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage331_runtime_integration_contract_disabled_by_default_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        builder = RuntimeIntegrationContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        validation = builder.validate_contract(contract)

        assert validation["valid"] is True
        assert builder.is_enabled(contract) is False
        assert contract["enabled"] is False
        assert contract["default_mode"] == "disabled"
        assert contract["required_boundaries"]["provider_runtime"] == "external"
        assert contract["required_boundaries"]["http_client"] == "forbidden"
        assert contract["required_boundaries"]["api_key"] == "forbidden"
        assert set(contract["required_inputs"]) == {"runtime_state", "scheduler_snapshot", "resume_plan"}
        assert set(contract["expected_outputs"]) == {"runtime_report", "export_outputs", "integration_status"}
        assert manifest["validation_commands"][-1] == "python ntpe_validate.py"

        bad_contract = {**contract, "enabled": True}
        assert builder.validate_contract(bad_contract)["valid"] is False
        assert builder.is_enabled(bad_contract) is False

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

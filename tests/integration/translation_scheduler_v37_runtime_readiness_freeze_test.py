from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_READINESS_RELEASE_ID,
    RUNTIME_READINESS_STAGES,
    RUNTIME_READINESS_STATUS,
    RuntimeReadinessDecision,
    RuntimeReadinessEvidenceCollector,
    RuntimeReadinessGateContract,
    RuntimeReadinessGateEvaluator,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v37_runtime_readiness_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration runtime readiness freeze secret"


def test_v37_runtime_readiness_freeze_manifest_decisions_and_boundaries() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = ["core.translation_engine.provider_runtime", "lts.txt_translation_runtime", "requests", "httpx"]
    before = {name: name in sys.modules for name in watched}
    try:
        assert RuntimeReadinessGateContract is not None
        assert RuntimeReadinessGateEvaluator is not None
        assert RuntimeReadinessEvidenceCollector is not None
        assert RuntimeReadinessDecision is not None
        assert RUNTIME_READINESS_STATUS == "frozen"
        assert RUNTIME_READINESS_STAGES == ("3.7.1", "3.7.2", "3.7.3", "3.7.4")

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        contract = RuntimeReadinessGateContract().build_contract()
        evidence = {
            "freezes": {name: True for name in contract["required_freezes"]},
            "checks": {name: True for name in contract["readiness_checks"]},
            "versions": {"gate": contract["version"]},
            "reports": {"freeze": {"status": "pass", "text": SECRET_TEXT}},
        }
        decider = RuntimeReadinessDecision()
        approved = decider.decide(contract, evidence)
        rejected = decider.decide(contract, None)

        assert manifest["release_id"] == RUNTIME_READINESS_RELEASE_ID
        assert manifest["frozen"] is True
        assert manifest["next_allowed_mode"] == "mock_only"
        assert manifest["real_runtime_allowed"] is False
        assert manifest["execution_allowed"] is False
        assert approved["decision"] == "approved_for_mock_only"
        assert approved["execution_allowed"] is False
        assert approved["real_runtime_allowed"] is False
        assert rejected["decision"] == "rejected"
        assert SECRET_TEXT not in str(approved)
        assert decider.validate_decision(approved)["valid"] is True
        assert decider.validate_decision(rejected)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

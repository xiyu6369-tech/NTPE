from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_READINESS_RELEASE_ID,
    RUNTIME_READINESS_STAGES,
    RUNTIME_READINESS_STATUS,
    RUNTIME_READINESS_VERSION,
    RuntimeReadinessDecision,
    RuntimeReadinessEvidenceCollector,
    RuntimeReadinessGateContract,
    RuntimeReadinessGateEvaluator,
)


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v37_runtime_readiness_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "runtime readiness freeze secret"


def _complete_evidence() -> dict:
    contract = RuntimeReadinessGateContract().build_contract()
    return {
        "freezes": {name: True for name in contract["required_freezes"]},
        "checks": {name: True for name in contract["readiness_checks"]},
        "versions": {"readiness": "TE-v3.7", "preflight": "TE-v3.6"},
        "reports": {"freeze": {"status": "pass"}, "decision": {"status": "metadata_only"}},
    }


def test_runtime_readiness_freeze_imports_and_metadata() -> None:
    module = importlib.import_module("core.translation_scheduler")

    assert RuntimeReadinessGateContract is not None
    assert RuntimeReadinessGateEvaluator is not None
    assert RuntimeReadinessEvidenceCollector is not None
    assert RuntimeReadinessDecision is not None
    assert module.RUNTIME_READINESS_VERSION == "TE-v3.7"
    assert RUNTIME_READINESS_VERSION == "TE-v3.7"
    assert RUNTIME_READINESS_RELEASE_ID == "TE-v3.7-runtime-readiness-freeze"
    assert RUNTIME_READINESS_STATUS == "frozen"
    assert RUNTIME_READINESS_STAGES == ("3.7.1", "3.7.2", "3.7.3", "3.7.4")


def test_runtime_readiness_freeze_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == "TE-v3.7"
    assert manifest["release_id"] == RUNTIME_READINESS_RELEASE_ID
    assert manifest["layer"] == "runtime_readiness_gate"
    assert manifest["frozen"] is True
    assert manifest["stages"] == ["3.7.1", "3.7.2", "3.7.3", "3.7.4"]
    assert manifest["decision_flow"] == ["contract", "evaluator", "evidence_collector", "decision"]
    assert manifest["default_mode"] == "disabled"
    assert manifest["next_allowed_mode"] == "mock_only"
    assert manifest["real_runtime_allowed"] is False
    assert manifest["execution_allowed"] is False
    assert manifest["runtime_touch_mode"] == "none"
    assert manifest["launcher_touch_mode"] == "none"
    assert manifest["provider_touch_mode"] == "none"
    assert "no_raw_source_text_text_or_chunks_retention" in manifest["guarantees"]
    assert "te_v36_runtime_safe_hook_preflight_freeze_preserved" in manifest["guarantees"]
    assert "python ntpe_validate.py" in manifest["validation_commands"]
    assert manifest["next_stage"] == "TE-v3.8 Controlled Runtime Integration Trial Planning"


def test_runtime_readiness_freeze_approved_and_rejected_decisions() -> None:
    decider = RuntimeReadinessDecision()
    evidence = _complete_evidence()
    evidence["reports"]["unsafe"] = {
        "source_text": SECRET_TEXT,
        "text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    approved = decider.decide(evidence_inputs=evidence)
    rejected = decider.decide(evidence_inputs={})

    assert approved["approved"] is True
    assert approved["decision"] == "approved_for_mock_only"
    assert approved["next_allowed_mode"] == "mock_only"
    assert approved["real_runtime_allowed"] is False
    assert approved["execution_allowed"] is False
    assert approved["readiness_report"]["next_allowed_mode"] == "mock_only"
    assert approved["readiness_report"]["real_runtime_allowed"] is False
    assert decider.validate_decision(approved)["valid"] is True
    assert SECRET_TEXT not in str(approved)

    assert rejected["approved"] is False
    assert rejected["decision"] == "rejected"
    assert rejected["real_runtime_allowed"] is False
    assert rejected["execution_allowed"] is False
    assert decider.validate_decision(rejected)["valid"] is True


def test_runtime_readiness_freeze_no_external_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = [
        "core.translation_engine.provider_runtime",
        "core.production_runtime",
        "lts.txt_translation_runtime",
        "requests",
        "httpx",
    ]
    before = {name: name in sys.modules for name in watched}
    try:
        test_runtime_readiness_freeze_approved_and_rejected_decisions()
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_readiness_freeze_imports_and_metadata()
    test_runtime_readiness_freeze_manifest()
    test_runtime_readiness_freeze_approved_and_rejected_decisions()
    test_runtime_readiness_freeze_no_external_side_effects()
    print("NTPE TE-v3.7 Runtime Readiness Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

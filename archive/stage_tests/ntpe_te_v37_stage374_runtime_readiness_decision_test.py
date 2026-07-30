from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeReadinessDecision, RuntimeReadinessGateContract


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def _complete_evidence() -> dict:
    contract = RuntimeReadinessGateContract().build_contract()
    return {
        "freezes": {name: True for name in contract["required_freezes"]},
        "checks": {name: True for name in contract["readiness_checks"]},
        "versions": {"contract": "TE-v3.7", "preflight": "TE-v3.6"},
        "reports": {"freeze": {"status": "pass"}, "boundary": {"status": "pass"}},
    }


def test_readiness_decision_approves_complete_evidence_for_mock_only() -> None:
    decider = RuntimeReadinessDecision()
    decision = decider.decide(evidence_inputs=_complete_evidence())

    assert decision["approved"] is True
    assert decision["decision"] == "approved_for_mock_only"
    assert decision["readiness_report"]["ready"] is True
    assert decision["evidence_summary"]["complete"] is True
    assert decision["missing_requirements"] == []
    assert decision["unsafe_conditions"] == []
    assert decision["next_allowed_mode"] == "mock_only"
    assert decision["real_runtime_allowed"] is False
    assert decision["execution_allowed"] is False
    assert decider.is_approved(decision) is True
    assert decider.validate_decision(decision)["valid"] is True


def test_readiness_decision_rejects_missing_and_unsafe_inputs() -> None:
    decider = RuntimeReadinessDecision()

    empty = decider.decide()
    assert empty["approved"] is False
    assert empty["decision"] == "rejected"
    assert set(empty["missing_requirements"]) >= {"freezes", "checks", "versions", "reports"}

    missing_freeze = _complete_evidence()
    missing_freeze["freezes"].pop("TE-v3.6")
    assert "TE-v3.6" in decider.decide(evidence_inputs=missing_freeze)["missing_requirements"]

    missing_check = _complete_evidence()
    missing_check["checks"].pop("preflight_present")
    assert "preflight_present" in decider.decide(evidence_inputs=missing_check)["missing_requirements"]

    incomplete = _complete_evidence()
    incomplete.pop("reports")
    assert decider.decide(evidence_inputs=incomplete)["evidence_summary"]["complete"] is False

    contract = RuntimeReadinessGateContract().build_contract()
    unsafe_contract = {**contract, "provider_touch_mode": "read", "real_translation": True}
    unsafe = decider.decide(unsafe_contract, _complete_evidence())
    assert unsafe["approved"] is False
    assert "provider_touch_mode_not_none" in unsafe["unsafe_conditions"]
    assert "real_translation_not_false" in unsafe["unsafe_conditions"]
    assert decider.is_approved(unsafe) is False
    assert decider.validate_decision(unsafe)["valid"] is True


def test_readiness_decision_removes_raw_text_and_has_no_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = ["core.translation_engine.provider_runtime", "lts.txt_translation_runtime", "requests", "httpx"]
    before = {name: name in sys.modules for name in watched}
    evidence = _complete_evidence()
    evidence["reports"]["unsafe"] = {
        "source_text": "raw source",
        "text": "raw output",
        "nested": {"chunks": ["raw chunk"], "status": "sanitized"},
    }
    try:
        decider = RuntimeReadinessDecision()
        decision = decider.decide(evidence_inputs=evidence)
        serialized = repr(decision)
        assert "raw source" not in serialized
        assert "raw output" not in serialized
        assert "raw chunk" not in serialized
        assert decider.validate_decision(decision)["valid"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_readiness_decision_approves_complete_evidence_for_mock_only()
    test_readiness_decision_rejects_missing_and_unsafe_inputs()
    test_readiness_decision_removes_raw_text_and_has_no_side_effects()
    print("NTPE TE-v3.7 Stage-3.7.4 Runtime Readiness Decision PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

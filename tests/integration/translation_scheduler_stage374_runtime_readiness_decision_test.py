from __future__ import annotations

from core.translation_scheduler import RuntimeReadinessDecision, RuntimeReadinessGateContract


def test_stage374_combines_contract_evidence_and_evaluator_without_execution() -> None:
    contract = RuntimeReadinessGateContract().build_contract()
    evidence = {
        "freezes": {name: True for name in contract["required_freezes"]},
        "checks": {name: True for name in contract["readiness_checks"]},
        "versions": {"gate": contract["version"]},
        "reports": {"readiness": {"status": "metadata_only"}},
    }
    decider = RuntimeReadinessDecision()
    decision = decider.decide(contract, evidence)

    assert decision["approved"] is True
    assert decision["decision"] == "approved_for_mock_only"
    assert decision["next_allowed_mode"] == "mock_only"
    assert decision["execution_allowed"] is False
    assert decision["real_runtime_allowed"] is False
    assert decider.validate_decision(decision)["valid"] is True

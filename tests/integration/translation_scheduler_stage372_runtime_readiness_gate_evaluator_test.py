from __future__ import annotations

from core.translation_scheduler import RuntimeReadinessGateContract, RuntimeReadinessGateEvaluator


def test_stage372_evaluates_only_supplied_mock_readiness_state() -> None:
    contract = RuntimeReadinessGateContract().build_contract()
    state = {
        "freezes": {name: True for name in contract["required_freezes"]},
        "checks": {name: True for name in contract["readiness_checks"]},
        "mode": "mock_only",
    }
    evaluator = RuntimeReadinessGateEvaluator()
    report = evaluator.evaluate(contract, state)

    assert report["ready"] is True
    assert report["status"] == "ready"
    assert report["next_allowed_mode"] == "mock_only"
    assert report["real_runtime_allowed"] is False
    assert report["metadata"]["state_source"] == "supplied_mapping"
    assert evaluator.validate_report(report)["valid"] is True

    state["checks"].pop("boundary_regression_present")
    blocked = evaluator.evaluate(contract, state)
    assert blocked["ready"] is False
    assert blocked["missing_checks"] == ["boundary_regression_present"]

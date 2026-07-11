from __future__ import annotations

from core.translation_scheduler import (
    RuntimeReadinessEvidenceCollector,
    RuntimeReadinessGateContract,
    RuntimeReadinessGateEvaluator,
)


def test_stage373_evidence_feeds_stage372_without_external_discovery() -> None:
    contract = RuntimeReadinessGateContract().build_contract()
    collector = RuntimeReadinessEvidenceCollector()
    evidence = collector.collect(
        {
            "freezes": {name: True for name in contract["required_freezes"]},
            "checks": {name: True for name in contract["readiness_checks"]},
            "versions": {"contract": contract["version"]},
            "reports": {"boundary": {"status": "pass"}},
        }
    )

    state = {
        "freezes": evidence["collected_freezes"],
        "checks": evidence["collected_checks"],
        "mode": "mock_only",
    }
    report = RuntimeReadinessGateEvaluator().evaluate(contract, state)

    assert collector.validate_evidence(evidence)["valid"] is True
    assert collector.summarize(evidence)["complete"] is True
    assert report["ready"] is True
    assert report["real_runtime_allowed"] is False

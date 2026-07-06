from core.intelligence.intelligence_contract import IntelligenceRuntimeContract
from core.intelligence.intelligence_freeze_events import INTELLIGENCE_FREEZE_COMPLETED
from core.intelligence.intelligence_freeze_manifest import IntelligenceFreezeManifest
from core.intelligence.intelligence_freeze_validator import IntelligenceFreezeValidator


def test_freeze_manifest_locks_stage16_modules():
    manifest = IntelligenceFreezeManifest()
    assert manifest.frozen is True
    assert manifest.stage == "Stage-16.8"
    assert "Context Intelligence Engine" in manifest.frozen_modules
    assert "Adaptive Translation Strategy" in manifest.frozen_modules


def test_runtime_contract_keeps_required_engines():
    contract = IntelligenceRuntimeContract()
    assert contract.compatibility_level == "backward-compatible"
    assert contract.required_engines() == (
        "context",
        "narrative",
        "character",
        "semantic",
        "memory",
        "strategy",
    )
    assert "analyze" in contract.frozen_public_methods()["IntelligenceRuntime"]


def test_freeze_validator_passes_and_emits_completion():
    validator = IntelligenceFreezeValidator()
    result = validator.validate()
    assert result.passed is True
    assert result.status == "PASS"
    assert validator.event_bus.events[-1].name == INTELLIGENCE_FREEZE_COMPLETED

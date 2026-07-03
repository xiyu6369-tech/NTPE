from compatibility import CompatibilityAuditRegistry

def test_translation_provider_quality_contracts_compatible():
    registry = CompatibilityAuditRegistry.default()
    assert registry.require("translation_contract").backward_compatible is True
    assert registry.require("provider_contract").backward_compatible is True
    assert registry.require("quality_contract").backward_compatible is True

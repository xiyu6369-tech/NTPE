from compatibility import CompatibilityAuditRegistry

def test_runtime_and_rest_contracts_compatible():
    registry = CompatibilityAuditRegistry.default()
    assert registry.require("runtime_api_contract").backward_compatible is True
    assert registry.require("external_rest_contract").backward_compatible is True

def test_cli_sdk_contracts_compatible():
    registry = CompatibilityAuditRegistry.default()
    assert registry.require("cli_contract").breaking_change_detected is False
    assert registry.require("sdk_contract").breaking_change_detected is False

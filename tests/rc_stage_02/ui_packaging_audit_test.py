from compatibility import CompatibilityAuditRegistry

def test_webui_packaging_release_contracts_compatible():
    registry = CompatibilityAuditRegistry.default()
    assert registry.require("web_ui_contract").backward_compatible is True
    assert registry.require("packaging_contract").backward_compatible is True
    assert registry.require("release_manifest").backward_compatible is True

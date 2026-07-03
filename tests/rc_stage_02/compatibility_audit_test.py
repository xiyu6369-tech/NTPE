from pathlib import Path
from compatibility import CompatibilityAuditRegistry, CompatibilityAuditRunner, build_compatibility_audit_manifest

ROOT = Path(__file__).resolve().parents[2]

def test_audit_registry_created():
    registry = CompatibilityAuditRegistry.default()
    assert "runtime_api_contract" in registry.names()
    assert "external_rest_contract" in registry.names()
    assert registry.validate()["valid"] is True

def test_audit_runner_passes():
    result = CompatibilityAuditRunner(ROOT).run()
    assert result["passed"] is True
    assert result["compatibility"]["breaking_change_detected"] is False

def test_manifest_written():
    built = build_compatibility_audit_manifest(ROOT)
    assert Path(built["manifest_path"]).exists()
    assert Path(built["hash_path"]).exists()
    assert built["result"]["status"] == "PASS"

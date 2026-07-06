from core.workflow.production_platform_freeze import ProductionPlatformFreeze


def test_stage17_8_freeze_audit_passes():
    result = ProductionPlatformFreeze().audit()
    assert result.success
    assert result.status == "frozen"
    assert result.checks["required_modules"]
    assert result.checks["runtime_execution"]


def test_stage17_8_manifest_preserves_compatibility_contract():
    result = ProductionPlatformFreeze().freeze()
    contract = result.manifest["compatibility_contract"]
    assert result.manifest["stage"] == "Stage-17.8"
    assert result.manifest["status"] == "frozen"
    assert any("additive" in item.lower() for item in contract)
    assert any("foundation v1.0" in item.lower() for item in contract)


def test_stage17_8_runtime_probe_keeps_stage17_7_operational():
    result = ProductionPlatformFreeze().audit()
    runtime_details = result.details["runtime_execution"]
    assert runtime_details["runtime_success"] is True
    assert runtime_details["runtime_status"] == "completed"
    assert "translation" in runtime_details["artifact_keys"]

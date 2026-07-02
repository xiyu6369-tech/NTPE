"""External API Freeze assertions for Stage-12.8."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import (
    EXTERNAL_API_FREEZE_STAGE,
    FROZEN_EXTERNAL_API_MODULES,
    FROZEN_EXTERNAL_API_ROUTES,
    ExternalApiFreezeValidator,
    create_external_api_freeze_report,
    create_rest_api,
)


def test_freeze_report_contract():
    report = create_external_api_freeze_report(source="stage-12.8-test")
    data = report.to_dict()
    assert data["stage"] == EXTERNAL_API_FREEZE_STAGE
    assert data["frozen"] is True
    assert data["additive_only"] is True
    assert data["uses_frozen_runtime_api_only"] is True
    assert "external_api.rest_api" in data["modules"]
    assert {"method": "GET", "path": "/health"} in data["routes"]
    assert "External API" in data["compatibility_surfaces"]


def test_external_api_freeze_validation():
    api = create_rest_api()
    validator = ExternalApiFreezeValidator()
    report = validator.validate_rest_api(api)
    assert report.frozen is True
    assert "external_api.rest_auth" in FROZEN_EXTERNAL_API_MODULES
    assert ("POST", "/v1/runtime/execute") in FROZEN_EXTERNAL_API_ROUTES


def test_external_api_runtime_boundary():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert manifest["runtime_api_stage"] == "11.1"
    assert manifest["session_api"]["uses_frozen_runtime_session_api_only"] is True
    assert manifest["resource_api"]["uses_frozen_runtime_resource_api_only"] is True


if __name__ == "__main__":
    test_freeze_report_contract()
    test_external_api_freeze_validation()
    test_external_api_runtime_boundary()
    print("PASS")

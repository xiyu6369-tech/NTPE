"""Runtime API Freeze assertions for Stage-11.8."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime_api import (
    RuntimeApi,
    RuntimeApiFreezeValidator,
    create_runtime_api_freeze_report,
    FROZEN_RUNTIME_API_MODULES,
    FROZEN_RUNTIME_API_OPERATIONS,
)


def test_freeze_report_contract():
    report = create_runtime_api_freeze_report(source="stage-11.8-test")
    data = report.to_dict()
    assert data["stage"] == "11.8"
    assert data["frozen"] is True
    assert data["additive_only"] is True
    assert "runtime_api.runtime_api" in data["modules"]
    assert "runtime.ping" in data["operations"]
    assert "Runtime Middleware" in data["compatibility_surfaces"]


def test_runtime_api_core_freeze_validation():
    api = RuntimeApi()
    validator = RuntimeApiFreezeValidator()
    report = validator.validate_runtime_api(api)
    assert report.frozen is True
    assert "runtime_api.middleware_api" in FROZEN_RUNTIME_API_MODULES
    assert "middleware.register" in FROZEN_RUNTIME_API_OPERATIONS


if __name__ == "__main__":
    test_freeze_report_contract()
    test_runtime_api_core_freeze_validation()
    print("PASS")

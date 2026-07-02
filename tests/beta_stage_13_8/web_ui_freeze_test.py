"""Web UI Freeze assertions for Stage-13.8."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_FREEZE_STAGE, create_web_ui_app, create_web_ui_freeze_report, validate_web_ui_freeze


def test_web_ui_freeze_report_created():
    app = create_web_ui_app()
    report = create_web_ui_freeze_report(app).to_dict()
    assert report["stage"] == WEB_UI_FREEZE_STAGE
    assert report["frozen"] is True
    assert report["uses_external_api_only"] is True
    assert report["uses_frozen_runtime_api_only"] is True


def test_web_ui_freeze_validation_passes():
    app = create_web_ui_app()
    result = validate_web_ui_freeze(app)
    assert result["passed"] is True
    assert all(result["checks"].values())


def test_web_ui_freeze_routes_are_present():
    app = create_web_ui_app()
    result = validate_web_ui_freeze(app)
    for path in ["/", "/sessions", "/jobs", "/pipelines", "/events", "/resources"]:
        assert path in result["routes"]


def test_web_ui_freeze_preserves_page_boundaries():
    app = create_web_ui_app()
    result = validate_web_ui_freeze(app)
    assert result["compatibility"]["dashboard_page"] is True
    assert result["compatibility"]["session_page"] is True
    assert result["compatibility"]["job_page"] is True
    assert result["compatibility"]["pipeline_page"] is True
    assert result["compatibility"]["event_page"] is True
    assert result["compatibility"]["resource_page"] is True


if __name__ == "__main__":
    test_web_ui_freeze_report_created()
    test_web_ui_freeze_validation_passes()
    test_web_ui_freeze_routes_are_present()
    test_web_ui_freeze_preserves_page_boundaries()
    print("PASS")

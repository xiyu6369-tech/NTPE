"""Web UI Dashboard assertions for Stage-13.2."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_DASHBOARD_STAGE, WebUiDashboard, create_web_ui_app


def test_dashboard_created():
    app = create_web_ui_app()
    view = app.dashboard_view()
    assert view["stage"] == WEB_UI_DASHBOARD_STAGE
    assert view["metadata"]["framework_neutral"] is True
    assert view["metadata"]["uses_web_ui_state_only"] is True
    assert len(view["metrics"]) >= 4
    assert len(view["sections"]) >= 2


def test_dashboard_render_component():
    app = create_web_ui_app()
    page = app.render("/").to_dict()
    dashboard_components = [component for component in page["components"] if component["type"] == "dashboard"]
    assert len(dashboard_components) == 1
    assert dashboard_components[0]["view"]["stage"] == WEB_UI_DASHBOARD_STAGE


def test_dashboard_summary():
    app = create_web_ui_app()
    state = app.client.state()
    summary = WebUiDashboard().summary(state)
    assert summary["stage"] == WEB_UI_DASHBOARD_STAGE
    assert summary["rest_api_available"] is True
    assert summary["framework_neutral"] is True


def test_dashboard_manifest():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["dashboard_stage"] == WEB_UI_DASHBOARD_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True


if __name__ == "__main__":
    test_dashboard_created()
    test_dashboard_render_component()
    test_dashboard_summary()
    test_dashboard_manifest()
    print("PASS")

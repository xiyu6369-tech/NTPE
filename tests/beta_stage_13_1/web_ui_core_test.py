"""Web UI Core assertions for Stage-13.1."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_STAGE, WebUiRoute, WebUiShell, create_web_ui_app


def test_web_ui_shell_created():
    shell = WebUiShell()
    manifest = shell.manifest()
    assert manifest["stage"] == WEB_UI_STAGE
    assert manifest["framework_neutral"] is True
    assert {"path": "/", "title": "Dashboard", "page_id": "dashboard", "navigation": True, "metadata": {}} in manifest["routes"]


def test_web_ui_route_registration():
    shell = WebUiShell()
    shell.register_route(WebUiRoute("/custom", "Custom", "custom"))
    assert shell.route("/custom").page_id == "custom"
    assert any(item["path"] == "/custom" for item in shell.navigation())


def test_web_ui_app_manifest_boundary():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["stage"] == WEB_UI_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert manifest["external_api_stage"] == "12.1"
    assert manifest["runtime_api_stage"] == "11.1"


def test_web_ui_render_dashboard():
    app = create_web_ui_app()
    page = app.render("/")
    data = page.to_dict()
    assert data["stage"] == WEB_UI_STAGE
    assert data["route"]["page_id"] == "dashboard"
    assert data["state"]["rest_api_available"] is True
    assert data["state"]["metadata"]["uses_external_api_only"] is True
    assert any(component["type"] == "navigation" for component in data["components"])


if __name__ == "__main__":
    test_web_ui_shell_created()
    test_web_ui_route_registration()
    test_web_ui_app_manifest_boundary()
    test_web_ui_render_dashboard()
    print("PASS")

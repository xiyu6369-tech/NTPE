"""Web UI Resource Page assertions for Stage-13.7."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_RESOURCE_STAGE, WebUiResourcePage, create_web_ui_app


def test_resource_page_created():
    app = create_web_ui_app()
    view = app.resource_view()
    assert view["stage"] == WEB_UI_RESOURCE_STAGE
    assert view["metadata"]["uses_rest_resource_api_only"] is True
    assert view["metadata"]["additive_only"] is True
    assert len(view["actions"]) >= 8


def test_resource_page_render_component():
    app = create_web_ui_app()
    page = app.render("/resources").to_dict()
    components = [component for component in page["components"] if component["type"] == "resource_page"]
    assert len(components) == 1
    assert components[0]["view"]["stage"] == WEB_UI_RESOURCE_STAGE


def test_resource_page_summary():
    app = create_web_ui_app()
    state = app.client.state()
    summary = WebUiResourcePage(app.client).summary(state)
    assert summary["stage"] == WEB_UI_RESOURCE_STAGE
    assert summary["uses_rest_resource_api_only"] is True
    assert summary["rest_api_available"] is True


def test_resource_page_manifest():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["resource_page_stage"] == WEB_UI_RESOURCE_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True


def test_resource_create_and_refresh():
    app = create_web_ui_app()
    created = app.client.create_resource(name="ui.resource.test", uri="memory://stage-13-7")
    assert created["status_code"] == 201
    view = app.resource_view()
    assert view["metadata"]["uses_rest_resource_api_only"] is True
    assert isinstance(view["resources"], list)
    assert len(view["resources"]) >= 1


if __name__ == "__main__":
    test_resource_page_created()
    test_resource_page_render_component()
    test_resource_page_summary()
    test_resource_page_manifest()
    test_resource_create_and_refresh()
    print("PASS")

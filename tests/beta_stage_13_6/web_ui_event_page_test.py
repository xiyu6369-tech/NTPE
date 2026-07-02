"""Web UI Event Page assertions for Stage-13.6."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_EVENT_STAGE, WebUiEventPage, create_web_ui_app


def test_event_page_created():
    app = create_web_ui_app()
    view = app.event_view()
    assert view["stage"] == WEB_UI_EVENT_STAGE
    assert view["metadata"]["uses_rest_event_api_only"] is True
    assert view["metadata"]["additive_only"] is True
    assert len(view["actions"]) >= 6


def test_event_page_render_component():
    app = create_web_ui_app()
    page = app.render("/events").to_dict()
    components = [component for component in page["components"] if component["type"] == "event_page"]
    assert len(components) == 1
    assert components[0]["view"]["stage"] == WEB_UI_EVENT_STAGE


def test_event_page_summary():
    app = create_web_ui_app()
    state = app.client.state()
    summary = WebUiEventPage(app.client).summary(state)
    assert summary["stage"] == WEB_UI_EVENT_STAGE
    assert summary["uses_rest_event_api_only"] is True
    assert summary["rest_api_available"] is True


def test_event_page_manifest():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["event_page_stage"] == WEB_UI_EVENT_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True


def test_event_publish_and_refresh():
    app = create_web_ui_app()
    published = app.client.publish_event(name="ui.event.test", message="Stage-13.6 event page test")
    assert published["status_code"] == 201
    view = app.event_view()
    assert view["metadata"]["uses_rest_event_api_only"] is True
    assert isinstance(view["events"], list)


if __name__ == "__main__":
    test_event_page_created()
    test_event_page_render_component()
    test_event_page_summary()
    test_event_page_manifest()
    test_event_publish_and_refresh()
    print("PASS")

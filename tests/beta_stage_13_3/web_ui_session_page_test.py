"""Web UI Session Page assertions for Stage-13.3."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_SESSION_STAGE, WebUiSessionPage, create_web_ui_app


def test_session_page_created():
    app = create_web_ui_app()
    view = app.session_view()
    assert view["stage"] == WEB_UI_SESSION_STAGE
    assert view["metadata"]["uses_rest_session_api_only"] is True
    assert view["metadata"]["additive_only"] is True
    assert len(view["actions"]) >= 6


def test_session_page_render_component():
    app = create_web_ui_app()
    page = app.render("/sessions").to_dict()
    components = [component for component in page["components"] if component["type"] == "session_page"]
    assert len(components) == 1
    assert components[0]["view"]["stage"] == WEB_UI_SESSION_STAGE


def test_session_page_summary():
    app = create_web_ui_app()
    state = app.client.state()
    summary = WebUiSessionPage(app.client).summary(state)
    assert summary["stage"] == WEB_UI_SESSION_STAGE
    assert summary["uses_rest_session_api_only"] is True
    assert summary["rest_api_available"] is True


def test_session_page_manifest():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["session_page_stage"] == WEB_UI_SESSION_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True


if __name__ == "__main__":
    test_session_page_created()
    test_session_page_render_component()
    test_session_page_summary()
    test_session_page_manifest()
    print("PASS")

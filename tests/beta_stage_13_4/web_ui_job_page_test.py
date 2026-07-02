"""Web UI Job Page assertions for Stage-13.4."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import WEB_UI_JOB_STAGE, WebUiJobPage, create_web_ui_app


def test_job_page_created():
    app = create_web_ui_app()
    view = app.job_view()
    assert view["stage"] == WEB_UI_JOB_STAGE
    assert view["metadata"]["uses_rest_job_api_only"] is True
    assert view["metadata"]["additive_only"] is True
    assert len(view["actions"]) >= 8


def test_job_page_render_component():
    app = create_web_ui_app()
    page = app.render("/jobs").to_dict()
    components = [component for component in page["components"] if component["type"] == "job_page"]
    assert len(components) == 1
    assert components[0]["view"]["stage"] == WEB_UI_JOB_STAGE


def test_job_page_summary():
    app = create_web_ui_app()
    state = app.client.state()
    summary = WebUiJobPage(app.client).summary(state)
    assert summary["stage"] == WEB_UI_JOB_STAGE
    assert summary["uses_rest_job_api_only"] is True
    assert summary["rest_api_available"] is True


def test_job_page_manifest():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["job_page_stage"] == WEB_UI_JOB_STAGE
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True


if __name__ == "__main__":
    test_job_page_created()
    test_job_page_render_component()
    test_job_page_summary()
    test_job_page_manifest()
    print("PASS")

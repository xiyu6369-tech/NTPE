"""Translation validation guard for Stage-13.1."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import create_web_ui_app


def test_translation_validation_stage_13_1():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True
    page = app.render("/jobs")
    data = page.to_dict()
    assert data["state"]["rest_api_available"] is True
    assert data["state"]["runtime_api_stage"] == "11.1"
    assert data["state"]["external_api_stage"] == "12.1"


if __name__ == "__main__":
    test_translation_validation_stage_13_1()
    print("PASS")

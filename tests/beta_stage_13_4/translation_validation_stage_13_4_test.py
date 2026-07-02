"""Translation validation guard for Stage-13.4."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import create_web_ui_app


def test_translation_validation_stage_13_4():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert manifest["job_page_stage"] == "13.4"
    page = app.render("/jobs").to_dict()
    assert page["state"]["rest_api_available"] is True
    assert any(component["type"] == "job_page" for component in page["components"])


if __name__ == "__main__":
    test_translation_validation_stage_13_4()
    print("PASS")

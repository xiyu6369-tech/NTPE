"""Translation validation guard for Stage-13.7."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import create_web_ui_app


def test_translation_validation_stage_13_7():
    app = create_web_ui_app()
    manifest = app.manifest()
    assert manifest["uses_external_api_only"] is True
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert manifest["resource_page_stage"] == "13.7"
    page = app.render("/resources").to_dict()
    assert page["state"]["rest_api_available"] is True
    assert any(component["type"] == "resource_page" for component in page["components"])


if __name__ == "__main__":
    test_translation_validation_stage_13_7()
    print("PASS")

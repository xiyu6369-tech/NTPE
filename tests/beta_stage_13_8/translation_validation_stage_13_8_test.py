"""Translation validation guard for Stage-13.8."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_ui import create_web_ui_app, validate_web_ui_freeze


def test_translation_validation_stage_13_8():
    app = create_web_ui_app()
    result = validate_web_ui_freeze(app)
    assert result["passed"] is True
    assert result["uses_external_api_only"] is True
    assert result["uses_frozen_runtime_api_only"] is True
    assert result["additive_only"] is True
    for path in ["/", "/sessions", "/jobs", "/pipelines", "/events", "/resources"]:
        rendered = app.render(path).to_dict()
        assert rendered["state"]["rest_api_available"] is True


if __name__ == "__main__":
    test_translation_validation_stage_13_8()
    print("PASS")

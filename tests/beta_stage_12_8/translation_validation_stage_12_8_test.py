"""Translation validation guard for Stage-12.8."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_8():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert manifest["runtime_api_stage"] == "11.1"
    assert manifest["session_api"]["additive_only"] is True
    assert manifest["job_api"]["additive_only"] is True
    assert manifest["pipeline_api"]["additive_only"] is True
    assert manifest["event_api"]["additive_only"] is True
    assert manifest["resource_api"]["additive_only"] is True
    response = api.handle("GET", "/health")
    assert response.status_code == 200
    assert response.body["ok"] is True


if __name__ == "__main__":
    test_translation_validation_stage_12_8()
    print("PASS")

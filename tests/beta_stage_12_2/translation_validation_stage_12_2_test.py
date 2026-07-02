"""Translation validation smoke test for Stage-12.2.

REST Session routes must preserve Runtime API compatibility while allowing
translation workflows to create resumable session state through the external API.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_2():
    api = create_rest_api()
    health = api.handle("GET", "/health")
    assert health.status_code == 200
    assert health.body["data"]["pong"] is True
    created = api.handle("POST", "/v1/sessions", body={"name": "translation-validation", "metadata": {"workflow": "translation"}})
    assert created.status_code == 201
    session_id = created.body["data"]["session_id"]
    activated = api.handle("POST", f"/v1/sessions/{session_id}/activate")
    assert activated.status_code == 200
    resume = api.handle("GET", f"/v1/sessions/{session_id}/resume-state")
    assert resume.status_code == 200
    assert resume.body["data"]["resumable"] is True


if __name__ == "__main__":
    test_translation_validation_stage_12_2()
    print("PASS")

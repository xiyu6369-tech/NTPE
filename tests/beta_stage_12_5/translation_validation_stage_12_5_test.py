"""Translation validation smoke test for Stage-12.5."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_5():
    api = create_rest_api()
    session = api.handle("POST", "/v1/sessions", body={"name": "translation-validation", "metadata": {"workflow": "translation"}})
    assert session.status_code == 201
    session_id = session.body["data"]["session_id"]
    job = api.handle("POST", "/v1/jobs", body={"session_id": session_id, "name": "translation-job", "provider": "validation-provider"})
    assert job.status_code == 201
    job_id = job.body["data"]["job_id"]
    event = api.handle("POST", "/v1/events", body={"name": "translation.job.created", "event_type": "job", "severity": "info", "job_id": job_id})
    assert event.status_code == 201
    filtered = api.handle("POST", "/v1/events/filter", body={"job_id": job_id})
    assert filtered.status_code == 200
    assert filtered.body["data"]["count"] == 1


if __name__ == "__main__":
    test_translation_validation_stage_12_5()
    print("PASS")

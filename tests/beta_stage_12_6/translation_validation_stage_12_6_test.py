"""Translation validation smoke test for Stage-12.6."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_6():
    api = create_rest_api()
    session = api.handle("POST", "/v1/sessions", body={"name": "translation-validation", "metadata": {"workflow": "translation"}})
    assert session.status_code == 201
    session_id = session.body["data"]["session_id"]
    resource = api.handle("POST", "/v1/resources", body={"name": "source-ko.txt", "resource_type": "input", "session_id": session_id})
    assert resource.status_code == 201
    resource_id = resource.body["data"]["resource_id"]
    job = api.handle("POST", "/v1/jobs", body={"session_id": session_id, "name": "translation-job", "input_ref": resource_id, "provider": "validation-provider"})
    assert job.status_code == 201
    job_id = job.body["data"]["job_id"]
    attached = api.handle("POST", f"/v1/resources/{resource_id}/attach", body={"job_id": job_id})
    assert attached.status_code == 200
    assert attached.body["data"]["job_id"] == job_id
    filtered = api.handle("POST", "/v1/resources/filter", body={"job_id": job_id})
    assert filtered.status_code == 200
    assert filtered.body["data"]["count"] == 1


if __name__ == "__main__":
    test_translation_validation_stage_12_6()
    print("PASS")

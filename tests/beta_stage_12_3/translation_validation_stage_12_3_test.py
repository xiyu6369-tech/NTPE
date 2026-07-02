"""Translation validation smoke test for Stage-12.3."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_3():
    api = create_rest_api()
    health = api.handle("GET", "/health")
    assert health.status_code == 200
    created_session = api.handle("POST", "/v1/sessions", body={"name": "translation-validation", "metadata": {"workflow": "translation"}})
    assert created_session.status_code == 201
    session_id = created_session.body["data"]["session_id"]
    created_job = api.handle(
        "POST",
        "/v1/jobs",
        body={
            "session_id": session_id,
            "name": "translation-job",
            "input_ref": "sample_ko.txt",
            "output_ref": "sample_zh.txt",
            "provider": "validation-provider",
            "pipeline": "translation",
        },
    )
    assert created_job.status_code == 201
    job_id = created_job.body["data"]["job_id"]
    started = api.handle("POST", f"/v1/jobs/{job_id}/start")
    assert started.status_code == 200
    status = api.handle("GET", f"/v1/jobs/{job_id}/status")
    assert status.status_code == 200
    assert status.body["data"]["session_id"] == session_id


if __name__ == "__main__":
    test_translation_validation_stage_12_3()
    print("PASS")

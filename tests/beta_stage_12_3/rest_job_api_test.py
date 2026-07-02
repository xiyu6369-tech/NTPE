"""Stage-12.3 REST Job API tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import REST_JOB_API_STAGE, RestApi, create_rest_api


def test_rest_job_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["job_api"]["stage"] == REST_JOB_API_STAGE
    assert manifest["job_api"]["uses_frozen_runtime_job_api_only"] is True
    assert ("POST", "/v1/jobs") in api.routes()
    assert ("GET", "/v1/jobs") in api.routes()


def test_create_get_list_job():
    api = create_rest_api()
    created = api.handle("POST", "/v1/jobs", body={"name": "demo-job", "input_ref": "in.txt", "output_ref": "out.txt", "provider": "mock"})
    assert created.status_code == 201
    assert created.body["ok"] is True
    job_id = created.body["data"]["job_id"]
    fetched = api.handle("GET", f"/v1/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.body["data"]["name"] == "demo-job"
    listed = api.handle("GET", "/v1/jobs")
    assert listed.status_code == 200
    assert listed.body["data"]["count"] == 1


def test_job_transitions_status_and_result():
    api = create_rest_api()
    created = api.handle("POST", "/v1/jobs", body={"name": "transition-job", "pipeline": "translation"})
    job_id = created.body["data"]["job_id"]
    started = api.handle("POST", f"/v1/jobs/{job_id}/start", body={"metadata": {"step": "start"}})
    assert started.status_code == 200
    assert started.body["data"]["state"] == "started"
    paused = api.handle("POST", f"/v1/jobs/{job_id}/pause")
    assert paused.status_code == 200
    assert paused.body["data"]["state"] == "paused"
    status = api.handle("GET", f"/v1/jobs/{job_id}/status")
    assert status.status_code == 200
    assert status.body["data"]["resumable"] is True
    completed = api.handle("POST", f"/v1/jobs/{job_id}/complete", body={"result": {"segments": 1}})
    assert completed.status_code == 200
    result = api.handle("GET", f"/v1/jobs/{job_id}/result")
    assert result.status_code == 200
    assert result.body["data"]["available"] is True
    assert result.body["data"]["result"]["segments"] == 1


def test_job_not_found():
    api = create_rest_api()
    response = api.handle("GET", "/v1/jobs/missing")
    assert response.status_code == 404
    assert response.body["ok"] is False


def test_method_validation():
    api = create_rest_api()
    created = api.handle("POST", "/v1/jobs", body={})
    job_id = created.body["data"]["job_id"]
    response = api.handle("GET", f"/v1/jobs/{job_id}/start")
    assert response.status_code == 405
    response2 = api.handle("POST", f"/v1/jobs/{job_id}/status")
    assert response2.status_code == 405


if __name__ == "__main__":
    test_rest_job_api_created()
    test_create_get_list_job()
    test_job_transitions_status_and_result()
    test_job_not_found()
    test_method_validation()
    print("PASS")

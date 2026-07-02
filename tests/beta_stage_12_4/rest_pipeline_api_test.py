"""Stage-12.4 REST Pipeline API tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import REST_PIPELINE_API_STAGE, create_rest_api


def test_rest_pipeline_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["pipeline_api"]["stage"] == REST_PIPELINE_API_STAGE
    assert manifest["pipeline_api"]["uses_frozen_runtime_pipeline_api_only"] is True
    assert ("POST", "/v1/pipelines") in api.routes()
    assert ("GET", "/v1/pipelines") in api.routes()


def test_create_get_list_pipeline():
    api = create_rest_api()
    created = api.handle(
        "POST",
        "/v1/pipelines",
        body={
            "name": "translation-pipeline",
            "provider": "mock",
            "workflow_ref": "workflow.translation",
            "stages": [{"name": "normalize", "order": 1}, {"name": "translate", "order": 2}],
        },
    )
    assert created.status_code == 201
    assert created.body["ok"] is True
    pipeline_id = created.body["data"]["pipeline_id"]
    fetched = api.handle("GET", f"/v1/pipelines/{pipeline_id}")
    assert fetched.status_code == 200
    assert fetched.body["data"]["name"] == "translation-pipeline"
    listed = api.handle("GET", "/v1/pipelines")
    assert listed.status_code == 200
    assert listed.body["data"]["count"] == 1


def test_add_stage_transitions_status_and_summary():
    api = create_rest_api()
    created = api.handle("POST", "/v1/pipelines", body={"name": "demo", "stages": [{"name": "normalize"}]})
    pipeline_id = created.body["data"]["pipeline_id"]
    added = api.handle("POST", f"/v1/pipelines/{pipeline_id}/stages", body={"stage": {"name": "translate", "order": 2}})
    assert added.status_code == 200
    assert added.body["data"]["stage_count"] == 2
    validated = api.handle("POST", f"/v1/pipelines/{pipeline_id}/validate")
    assert validated.status_code == 200
    assert validated.body["data"]["state"] == "validated"
    started = api.handle("POST", f"/v1/pipelines/{pipeline_id}/start")
    assert started.status_code == 200
    assert started.body["data"]["state"] == "started"
    status = api.handle("GET", f"/v1/pipelines/{pipeline_id}/status")
    assert status.status_code == 200
    assert status.body["data"]["resumable"] is True
    completed = api.handle("POST", f"/v1/pipelines/{pipeline_id}/complete", body={"result": {"segments": 2}})
    assert completed.status_code == 200
    summary = api.handle("GET", f"/v1/pipelines/{pipeline_id}/summary")
    assert summary.status_code == 200
    assert summary.body["data"]["result"]["segments"] == 2


def test_pipeline_not_found():
    api = create_rest_api()
    response = api.handle("GET", "/v1/pipelines/missing")
    assert response.status_code == 404
    assert response.body["ok"] is False


def test_method_validation():
    api = create_rest_api()
    created = api.handle("POST", "/v1/pipelines", body={"stages": [{"name": "normalize"}]})
    pipeline_id = created.body["data"]["pipeline_id"]
    response = api.handle("GET", f"/v1/pipelines/{pipeline_id}/start")
    assert response.status_code == 405
    response2 = api.handle("POST", f"/v1/pipelines/{pipeline_id}/status")
    assert response2.status_code == 405


if __name__ == "__main__":
    test_rest_pipeline_api_created()
    test_create_get_list_pipeline()
    test_add_stage_transitions_status_and_summary()
    test_pipeline_not_found()
    test_method_validation()
    print("PASS")

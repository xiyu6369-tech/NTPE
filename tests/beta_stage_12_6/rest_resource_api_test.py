"""Stage-12.6 REST Resource API tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import REST_RESOURCE_API_STAGE, create_rest_api


def test_rest_resource_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["resource_api"]["stage"] == REST_RESOURCE_API_STAGE
    assert manifest["resource_api"]["uses_frozen_runtime_resource_api_only"] is True
    assert ("POST", "/v1/resources") in api.routes()
    assert ("GET", "/v1/resources") in api.routes()


def test_create_get_list_resource():
    api = create_rest_api()
    created = api.handle(
        "POST",
        "/v1/resources",
        body={"name": "input.txt", "resource_type": "input", "uri": "file://input.txt", "size": 128},
    )
    assert created.status_code == 201
    assert created.body["ok"] is True
    resource_id = created.body["data"]["resource_id"]
    fetched = api.handle("GET", f"/v1/resources/{resource_id}")
    assert fetched.status_code == 200
    assert fetched.body["data"]["name"] == "input.txt"
    listed = api.handle("GET", "/v1/resources")
    assert listed.status_code == 200
    assert listed.body["data"]["count"] == 1


def test_filter_and_summary_resources():
    api = create_rest_api()
    api.handle("POST", "/v1/resources", body={"name": "input.txt", "resource_type": "input", "session_id": "session-1", "size": 100})
    api.handle("POST", "/v1/resources", body={"name": "output.txt", "resource_type": "output", "session_id": "session-1", "size": 200})
    filtered = api.handle("POST", "/v1/resources/filter", body={"resource_type": "output"})
    assert filtered.status_code == 200
    assert filtered.body["data"]["count"] == 1
    assert filtered.body["data"]["resources"][0]["name"] == "output.txt"
    summary = api.handle("GET", "/v1/resources/summary")
    assert summary.status_code == 200
    assert summary.body["data"]["count"] == 2
    assert summary.body["data"]["by_type"]["input"] == 1
    assert summary.body["data"]["total_size"] == 300


def test_resource_lifecycle_actions():
    api = create_rest_api()
    created = api.handle("POST", "/v1/resources", body={"name": "cache.bin", "resource_type": "cache"})
    resource_id = created.body["data"]["resource_id"]
    reserved = api.handle("POST", f"/v1/resources/{resource_id}/reserve", body={"metadata": {"reason": "test"}})
    assert reserved.status_code == 200
    assert reserved.body["data"]["state"] == "reserved"
    attached = api.handle("POST", f"/v1/resources/{resource_id}/attach", body={"job_id": "job-1"})
    assert attached.status_code == 200
    assert attached.body["data"]["state"] == "attached"
    assert attached.body["data"]["job_id"] == "job-1"
    released = api.handle("POST", f"/v1/resources/{resource_id}/release")
    assert released.status_code == 200
    assert released.body["data"]["state"] == "released"
    deleted = api.handle("POST", f"/v1/resources/{resource_id}/delete")
    assert deleted.status_code == 200
    assert deleted.body["data"]["state"] == "deleted"


def test_resource_not_found_and_method_validation():
    api = create_rest_api()
    response = api.handle("GET", "/v1/resources/missing")
    assert response.status_code == 404
    invalid = api.handle("POST", "/v1/resources/summary")
    assert invalid.status_code == 405


if __name__ == "__main__":
    test_rest_resource_api_created()
    test_create_get_list_resource()
    test_filter_and_summary_resources()
    test_resource_lifecycle_actions()
    test_resource_not_found_and_method_validation()
    print("PASS")

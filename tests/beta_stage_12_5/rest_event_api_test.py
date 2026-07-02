"""Stage-12.5 REST Event API tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import REST_EVENT_API_STAGE, create_rest_api


def test_rest_event_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["event_api"]["stage"] == REST_EVENT_API_STAGE
    assert manifest["event_api"]["uses_frozen_runtime_event_api_only"] is True
    assert ("POST", "/v1/events") in api.routes()
    assert ("GET", "/v1/events") in api.routes()


def test_publish_get_list_event():
    api = create_rest_api()
    created = api.handle(
        "POST",
        "/v1/events",
        body={
            "name": "translation.started",
            "event_type": "job",
            "severity": "info",
            "source": "rest-test",
            "job_id": "job-1",
            "payload": {"segments": 3},
        },
    )
    assert created.status_code == 201
    assert created.body["ok"] is True
    event_id = created.body["data"]["event_id"]
    fetched = api.handle("GET", f"/v1/events/{event_id}")
    assert fetched.status_code == 200
    assert fetched.body["data"]["name"] == "translation.started"
    listed = api.handle("GET", "/v1/events")
    assert listed.status_code == 200
    assert listed.body["data"]["count"] == 1


def test_filter_summary_and_clear_events():
    api = create_rest_api()
    api.handle("POST", "/v1/events", body={"name": "job.created", "event_type": "job", "severity": "info", "job_id": "job-1"})
    api.handle("POST", "/v1/events", body={"name": "pipeline.warning", "event_type": "pipeline", "severity": "warning", "pipeline_id": "pipe-1"})
    filtered = api.handle("POST", "/v1/events/filter", body={"severity": "warning"})
    assert filtered.status_code == 200
    assert filtered.body["data"]["count"] == 1
    assert filtered.body["data"]["events"][0]["name"] == "pipeline.warning"
    summary = api.handle("GET", "/v1/events/summary")
    assert summary.status_code == 200
    assert summary.body["data"]["count"] == 2
    assert summary.body["data"]["by_severity"]["warning"] == 1
    cleared = api.handle("POST", "/v1/events/clear")
    assert cleared.status_code == 200
    assert cleared.body["data"]["cleared"] == 2


def test_event_not_found():
    api = create_rest_api()
    response = api.handle("GET", "/v1/events/missing")
    assert response.status_code == 404
    assert response.body["ok"] is False


def test_method_validation():
    api = create_rest_api()
    response = api.handle("POST", "/v1/events/summary")
    assert response.status_code == 405


if __name__ == "__main__":
    test_rest_event_api_created()
    test_publish_get_list_event()
    test_filter_summary_and_clear_events()
    test_event_not_found()
    test_method_validation()
    print("PASS")

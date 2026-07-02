"""Stage-12.2 REST Session API tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import REST_SESSION_API_STAGE, RestApi, create_rest_api


def test_rest_session_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["session_api"]["stage"] == REST_SESSION_API_STAGE
    assert manifest["session_api"]["uses_frozen_runtime_session_api_only"] is True
    assert ("POST", "/v1/sessions") in api.routes()
    assert ("GET", "/v1/sessions") in api.routes()


def test_create_get_list_session():
    api = create_rest_api()
    created = api.handle("POST", "/v1/sessions", body={"name": "demo", "metadata": {"source": "test"}})
    assert created.status_code == 201
    assert created.body["ok"] is True
    session_id = created.body["data"]["session_id"]
    fetched = api.handle("GET", f"/v1/sessions/{session_id}")
    assert fetched.status_code == 200
    assert fetched.body["data"]["name"] == "demo"
    listed = api.handle("GET", "/v1/sessions")
    assert listed.status_code == 200
    assert listed.body["data"]["count"] == 1


def test_session_transitions_and_resume_state():
    api = create_rest_api()
    created = api.handle("POST", "/v1/sessions", body={"name": "transition"})
    session_id = created.body["data"]["session_id"]
    active = api.handle("POST", f"/v1/sessions/{session_id}/activate", body={"metadata": {"step": "active"}})
    assert active.status_code == 200
    assert active.body["data"]["state"] == "active"
    paused = api.handle("POST", f"/v1/sessions/{session_id}/pause")
    assert paused.status_code == 200
    assert paused.body["data"]["state"] == "paused"
    resume = api.handle("GET", f"/v1/sessions/{session_id}/resume-state")
    assert resume.status_code == 200
    assert resume.body["data"]["resumable"] is True


def test_session_not_found():
    api = create_rest_api()
    response = api.handle("GET", "/v1/sessions/missing")
    assert response.status_code == 404
    assert response.body["ok"] is False


def test_method_validation():
    api = create_rest_api()
    created = api.handle("POST", "/v1/sessions", body={})
    session_id = created.body["data"]["session_id"]
    response = api.handle("GET", f"/v1/sessions/{session_id}/activate")
    assert response.status_code == 405


if __name__ == "__main__":
    test_rest_session_api_created()
    test_create_get_list_session()
    test_session_transitions_and_resume_state()
    test_session_not_found()
    test_method_validation()
    print("PASS")

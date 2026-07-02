"""Stage-12.1 External API / REST Core tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import RestApi, RestRequest, RestResponse, create_rest_api
from runtime_api import RuntimeApi


def test_rest_models():
    request = RestRequest(method="get", path="health", body={"x": 1})
    assert request.method == "GET"
    assert request.path == "/health"
    response = RestResponse.ok({"ok": True})
    assert response.status_code == 200
    assert response.headers["x-ntpe-stage"] == "12.1"


def test_rest_api_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["stage"] == "12.1"
    assert manifest["uses_frozen_runtime_api_only"] is True
    assert ("GET", "/health") in api.routes()


def test_health_route():
    api = RestApi(RuntimeApi())
    response = api.handle("GET", "/health")
    assert response.status_code == 200
    assert response.body["ok"] is True
    assert response.body["data"]["pong"] is True


def test_runtime_execute_route():
    api = create_rest_api()
    response = api.handle("POST", "/v1/runtime/execute", body={"operation": "runtime.ping"})
    assert response.status_code == 200
    assert response.body["ok"] is True
    assert response.body["data"]["pong"] is True


def test_runtime_execute_validation():
    api = create_rest_api()
    response = api.handle("POST", "/v1/runtime/execute", body={})
    assert response.status_code == 400
    assert response.body["ok"] is False


def test_unknown_route():
    api = create_rest_api()
    response = api.handle("GET", "/missing")
    assert response.status_code == 404


if __name__ == "__main__":
    test_rest_models()
    test_rest_api_created()
    test_health_route()
    test_runtime_execute_route()
    test_runtime_execute_validation()
    test_unknown_route()
    print("PASS")

"""Stage-12.7 REST Middleware / Auth Hooks tests."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import (
    REST_AUTH_API_STAGE,
    REST_MIDDLEWARE_API_STAGE,
    RestResponse,
    create_rest_api,
)


def test_rest_middleware_auth_created():
    api = create_rest_api()
    manifest = api.manifest()
    assert manifest["middleware_api"]["stage"] == REST_MIDDLEWARE_API_STAGE
    assert manifest["auth_hooks"]["stage"] == REST_AUTH_API_STAGE
    assert manifest["middleware_api"]["uses_frozen_runtime_api_only"] is True
    assert manifest["auth_hooks"]["default_policy"] == "allow_when_no_hooks"


def test_default_auth_is_backward_compatible():
    api = create_rest_api()
    response = api.handle("GET", "/health")
    assert response.status_code == 200
    assert response.body["ok"] is True


def test_required_header_auth_hook():
    api = create_rest_api()
    api.auth_hooks.require_header("x-ntpe-token", "secret")
    denied = api.handle("GET", "/health")
    assert denied.status_code == 401
    assert denied.body["ok"] is False
    allowed = api.handle("GET", "/health", headers={"x-ntpe-token": "secret"})
    assert allowed.status_code == 200
    assert allowed.body["ok"] is True


def test_before_middleware_can_short_circuit():
    api = create_rest_api()

    def block_manifest(context):
        if context.request.path == "/v1/runtime/manifest":
            return RestResponse.error(403, "blocked by middleware", request_id=context.request.request_id)
        return None

    api.middleware.add_before(block_manifest)
    response = api.handle("GET", "/v1/runtime/manifest", request_id="req-block")
    assert response.status_code == 403
    assert response.request_id == "req-block"
    assert response.body["error"]["message"] == "blocked by middleware"


def test_after_middleware_can_annotate_response():
    api = create_rest_api()

    def annotate(context, response):
        headers = dict(response.headers)
        headers["x-ntpe-middleware"] = "stage-12.7"
        return RestResponse(status_code=response.status_code, body=response.body, headers=headers, request_id=response.request_id)

    api.middleware.add_after(annotate)
    response = api.handle("GET", "/health")
    assert response.status_code == 200
    assert response.headers["x-ntpe-middleware"] == "stage-12.7"


if __name__ == "__main__":
    test_rest_middleware_auth_created()
    test_default_auth_is_backward_compatible()
    test_required_header_auth_hook()
    test_before_middleware_can_short_circuit()
    test_after_middleware_can_annotate_response()
    print("PASS")

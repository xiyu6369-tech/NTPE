"""NTPE External API / REST Core for Stage-12.1."""
from __future__ import annotations

from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, RuntimeApiResponse, create_runtime_api

from .rest_models import EXTERNAL_API_STAGE, EXTERNAL_API_VERSION, RestRequest, RestResponse
from .rest_router import RestRouter
from .rest_session import RestSessionApi


class RestApi:
    """REST facade backed only by the frozen Runtime API surface."""

    version = EXTERNAL_API_VERSION
    stage = EXTERNAL_API_STAGE

    def __init__(self, runtime_api: Optional[RuntimeApi] = None) -> None:
        self.runtime_api = runtime_api or create_runtime_api()
        self.router = RestRouter()
        self.session_routes = RestSessionApi(self.runtime_api)
        self._register_core_routes()
        self.session_routes.register_routes(self.router)

    def _register_core_routes(self) -> None:
        self.router.add_route("GET", "/health", self._health)
        self.router.add_route("GET", "/v1/runtime/manifest", self._runtime_manifest)
        self.router.add_route("POST", "/v1/runtime/execute", self._runtime_execute)

    def routes(self) -> tuple[tuple[str, str], ...]:
        return self.router.routes()

    def handle(self, method: str, path: str, *, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, query: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> RestResponse:
        request = RestRequest(method=method, path=path, body=dict(body or {}), headers=dict(headers or {}), query=dict(query or {}), request_id=request_id)
        session_response = self.session_routes.maybe_dispatch(request)
        if session_response is not None:
            return session_response
        return self.router.dispatch(request)

    def _health(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("runtime.ping")
        return self._from_runtime_response(response, request=request, ok_status=200)

    def _runtime_manifest(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("runtime.manifest")
        return self._from_runtime_response(response, request=request, ok_status=200)

    def _runtime_execute(self, request: RestRequest) -> RestResponse:
        operation = request.body.get("operation")
        payload = request.body.get("payload", {})
        metadata = request.body.get("metadata", {})
        if not operation:
            return RestResponse.error(400, "operation is required", request_id=request.request_id)
        response = self.runtime_api.execute(str(operation), dict(payload or {}), metadata=dict(metadata or {}))
        return self._from_runtime_response(response, request=request, ok_status=200)

    def _from_runtime_response(self, response: RuntimeApiResponse, *, request: RestRequest, ok_status: int = 200) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage}
        if response.ok:
            return RestResponse(status_code=ok_status, body=body, request_id=request.request_id or response.request_id)
        status = 404 if response.error and response.error.code == "RuntimeApiNotFoundError" else 500
        return RestResponse(status_code=status, body=body, request_id=request.request_id or response.request_id)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "routes": [{"method": method, "path": path} for method, path in self.routes()],
            "runtime_api_version": self.runtime_api.version,
            "runtime_api_stage": self.runtime_api.stage,
            "additive_only": True,
            "uses_frozen_runtime_api_only": True,
            "session_api": self.session_routes.manifest(),
        }


def create_rest_api(runtime_api: Optional[RuntimeApi] = None) -> RestApi:
    return RestApi(runtime_api=runtime_api)

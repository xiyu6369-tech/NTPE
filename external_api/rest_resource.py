"""REST Resource API adapter for NTPE 1.0 Beta Stage-12.6.

This module is additive. It exposes HTTP-like resource routes while delegating
all resource operations to the frozen Runtime Resource API operation surface.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, attach_resource_api

from .rest_models import RestRequest, RestResponse
from .rest_router import RestRouter

REST_RESOURCE_API_VERSION = "1.0.0-beta.12.6"
REST_RESOURCE_API_STAGE = "12.6"

_RESOURCE_PATH = re.compile(r"^/v1/resources/([^/]+)(?:/([^/]+))?$")
_ACTION_TO_OPERATION = {
    "reserve": "resource.reserve",
    "attach": "resource.attach",
    "release": "resource.release",
    "delete": "resource.delete",
    "summary": "resource.summary",
}
_READ_ACTIONS = {"summary"}


class RestResourceApi:
    """REST route adapter backed by Runtime Resource API operations."""

    version = REST_RESOURCE_API_VERSION
    stage = REST_RESOURCE_API_STAGE

    def __init__(self, runtime_api: RuntimeApi) -> None:
        self.runtime_api = runtime_api
        self.resource_api = attach_resource_api(runtime_api)

    def register_routes(self, router: RestRouter) -> None:
        router.add_route("POST", "/v1/resources", self.create_resource)
        router.add_route("GET", "/v1/resources", self.list_resources)
        router.add_route("POST", "/v1/resources/filter", self.filter_resources)
        router.add_route("GET", "/v1/resources/summary", self.summary)

    def maybe_dispatch(self, request: RestRequest) -> Optional[RestResponse]:
        if request.path == "/v1/resources/summary":
            if request.method != "GET":
                return RestResponse.error(405, "method not allowed for resource summary", request_id=request.request_id)
            return self.summary(request)
        if request.path in {"/v1/resources", "/v1/resources/filter"}:
            return None
        match = _RESOURCE_PATH.match(request.path)
        if not match:
            return None
        resource_id, action = match.groups()
        if action is None and request.method == "GET":
            return self.get_resource(request, resource_id)
        if action in _ACTION_TO_OPERATION:
            if action in _READ_ACTIONS and request.method != "GET":
                return RestResponse.error(405, "method not allowed for resource read action", request_id=request.request_id)
            if action not in _READ_ACTIONS and request.method != "POST":
                return RestResponse.error(405, "method not allowed for resource transition", request_id=request.request_id)
            return self.resource_action(request, resource_id, action)
        return RestResponse.error(404, "REST resource route not found", request_id=request.request_id, details={"path": request.path})

    def create_resource(self, request: RestRequest) -> RestResponse:
        payload = {
            "name": request.body.get("name"),
            "resource_type": request.body.get("resource_type", "custom"),
            "uri": request.body.get("uri"),
            "owner_id": request.body.get("owner_id"),
            "session_id": request.body.get("session_id"),
            "job_id": request.body.get("job_id"),
            "pipeline_id": request.body.get("pipeline_id"),
            "size": request.body.get("size"),
            "metadata": dict(request.body.get("metadata") or {}),
        }
        response = self.runtime_api.execute("resource.create", payload)
        return self._runtime_response(response, request=request, ok_status=201)

    def list_resources(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("resource.list")
        return self._runtime_response(response, request=request, ok_status=200)

    def get_resource(self, request: RestRequest, resource_id: str) -> RestResponse:
        response = self.runtime_api.execute("resource.get", {"resource_id": resource_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def filter_resources(self, request: RestRequest) -> RestResponse:
        payload = {
            "resource_type": request.body.get("resource_type") or request.query.get("resource_type"),
            "state": request.body.get("state") or request.query.get("state"),
            "owner_id": request.body.get("owner_id") or request.query.get("owner_id"),
            "session_id": request.body.get("session_id") or request.query.get("session_id"),
            "job_id": request.body.get("job_id") or request.query.get("job_id"),
            "pipeline_id": request.body.get("pipeline_id") or request.query.get("pipeline_id"),
        }
        response = self.runtime_api.execute("resource.filter", {key: value for key, value in payload.items() if value is not None})
        return self._runtime_response(response, request=request, ok_status=200)

    def summary(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("resource.summary")
        return self._runtime_response(response, request=request, ok_status=200)

    def resource_action(self, request: RestRequest, resource_id: str, action: str) -> RestResponse:
        operation = _ACTION_TO_OPERATION[action]
        payload: Dict[str, Any] = {"resource_id": resource_id}
        if action in {"reserve", "release", "delete"}:
            payload["metadata"] = dict(request.body.get("metadata") or {})
        if action == "attach":
            payload.update(
                {
                    "owner_id": request.body.get("owner_id"),
                    "session_id": request.body.get("session_id"),
                    "job_id": request.body.get("job_id"),
                    "pipeline_id": request.body.get("pipeline_id"),
                    "metadata": dict(request.body.get("metadata") or {}),
                }
            )
        response = self.runtime_api.execute(operation, payload)
        return self._runtime_response(response, request=request, ok_status=200)

    def _runtime_response(self, response: Any, *, request: RestRequest, ok_status: int) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage, "resource": "resource"}
        if response.ok:
            return RestResponse(status_code=ok_status, body=body, request_id=request.request_id or response.request_id)
        error = body.get("error") if isinstance(body.get("error"), dict) else {}
        error_code = str(error.get("code") or "")
        error_cause = str(error.get("cause") or "")
        error_status = int(error.get("status") or 500)
        status = 404 if error_code in {"RuntimeApiNotFoundError", "runtime_api_not_found"} or "RuntimeApiNotFoundError" in error_cause else error_status
        return RestResponse(status_code=status, body=body, request_id=request.request_id or response.request_id)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "routes": [
                {"method": "POST", "path": "/v1/resources"},
                {"method": "GET", "path": "/v1/resources"},
                {"method": "GET", "path": "/v1/resources/{resource_id}"},
                {"method": "POST", "path": "/v1/resources/filter"},
                {"method": "POST", "path": "/v1/resources/{resource_id}/reserve"},
                {"method": "POST", "path": "/v1/resources/{resource_id}/attach"},
                {"method": "POST", "path": "/v1/resources/{resource_id}/release"},
                {"method": "POST", "path": "/v1/resources/{resource_id}/delete"},
                {"method": "GET", "path": "/v1/resources/summary"},
            ],
            "runtime_operations": list(self.resource_api.operations),
            "uses_frozen_runtime_resource_api_only": True,
            "additive_only": True,
        }

"""REST Event API adapter for NTPE 1.0 Beta Stage-12.5.

This module is additive. It exposes HTTP-like event routes while delegating
all event operations to the frozen Runtime Event API operation surface.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, attach_event_api

from .rest_models import RestRequest, RestResponse
from .rest_router import RestRouter

REST_EVENT_API_VERSION = "1.0.0-beta.12.5"
REST_EVENT_API_STAGE = "12.5"

_EVENT_PATH = re.compile(r"^/v1/events/([^/]+)(?:/([^/]+))?$")
_ACTION_TO_OPERATION = {
    "summary": "event.summary",
}


class RestEventApi:
    """REST route adapter backed by Runtime Event API operations."""

    version = REST_EVENT_API_VERSION
    stage = REST_EVENT_API_STAGE

    def __init__(self, runtime_api: RuntimeApi) -> None:
        self.runtime_api = runtime_api
        self.event_api = attach_event_api(runtime_api)

    def register_routes(self, router: RestRouter) -> None:
        router.add_route("POST", "/v1/events", self.publish_event)
        router.add_route("GET", "/v1/events", self.list_events)
        router.add_route("POST", "/v1/events/filter", self.filter_events)
        router.add_route("GET", "/v1/events/summary", self.summary)
        router.add_route("POST", "/v1/events/clear", self.clear_events)

    def maybe_dispatch(self, request: RestRequest) -> Optional[RestResponse]:
        if request.path == "/v1/events/summary":
            if request.method != "GET":
                return RestResponse.error(405, "method not allowed for event summary", request_id=request.request_id)
            return self.summary(request)
        if request.path in {"/v1/events", "/v1/events/filter", "/v1/events/clear"}:
            return None
        match = _EVENT_PATH.match(request.path)
        if not match:
            return None
        event_id, action = match.groups()
        if action is None and request.method == "GET":
            return self.get_event(request, event_id)
        if action in _ACTION_TO_OPERATION:
            if request.method != "GET":
                return RestResponse.error(405, "method not allowed for event read action", request_id=request.request_id)
            return self.event_action(request, event_id, action)
        return RestResponse.error(404, "REST event route not found", request_id=request.request_id, details={"path": request.path})

    def publish_event(self, request: RestRequest) -> RestResponse:
        payload = {
            "name": request.body.get("name") or request.body.get("event") or "runtime.event",
            "event_type": request.body.get("event_type", "custom"),
            "severity": request.body.get("severity", "info"),
            "source": request.body.get("source"),
            "session_id": request.body.get("session_id"),
            "job_id": request.body.get("job_id"),
            "pipeline_id": request.body.get("pipeline_id"),
            "message": request.body.get("message"),
            "payload": dict(request.body.get("payload") or {}),
            "metadata": dict(request.body.get("metadata") or {}),
        }
        response = self.runtime_api.execute("event.publish", payload)
        return self._runtime_response(response, request=request, ok_status=201)

    def list_events(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("event.list")
        return self._runtime_response(response, request=request, ok_status=200)

    def get_event(self, request: RestRequest, event_id: str) -> RestResponse:
        response = self.runtime_api.execute("event.get", {"event_id": event_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def filter_events(self, request: RestRequest) -> RestResponse:
        payload = {
            "event_type": request.body.get("event_type") or request.query.get("event_type"),
            "severity": request.body.get("severity") or request.query.get("severity"),
            "session_id": request.body.get("session_id") or request.query.get("session_id"),
            "job_id": request.body.get("job_id") or request.query.get("job_id"),
            "pipeline_id": request.body.get("pipeline_id") or request.query.get("pipeline_id"),
        }
        response = self.runtime_api.execute("event.filter", {key: value for key, value in payload.items() if value is not None})
        return self._runtime_response(response, request=request, ok_status=200)

    def summary(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("event.summary")
        return self._runtime_response(response, request=request, ok_status=200)

    def clear_events(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("event.clear")
        return self._runtime_response(response, request=request, ok_status=200)

    def event_action(self, request: RestRequest, event_id: str, action: str) -> RestResponse:
        operation = _ACTION_TO_OPERATION[action]
        response = self.runtime_api.execute(operation, {"event_id": event_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def _runtime_response(self, response: Any, *, request: RestRequest, ok_status: int) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage, "resource": "event"}
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
                {"method": "POST", "path": "/v1/events"},
                {"method": "GET", "path": "/v1/events"},
                {"method": "GET", "path": "/v1/events/{event_id}"},
                {"method": "POST", "path": "/v1/events/filter"},
                {"method": "GET", "path": "/v1/events/summary"},
                {"method": "POST", "path": "/v1/events/clear"},
            ],
            "runtime_operations": list(self.event_api.operations),
            "uses_frozen_runtime_event_api_only": True,
            "additive_only": True,
        }

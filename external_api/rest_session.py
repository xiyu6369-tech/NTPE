"""REST Session API adapter for NTPE 1.0 Beta Stage-12.2.

This module is additive. It exposes HTTP-like session routes while delegating
all session state changes to the frozen Runtime Session API operation surface.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, attach_session_api

from .rest_models import RestRequest, RestResponse
from .rest_router import RestRouter

REST_SESSION_API_VERSION = "1.0.0-beta.12.2"
REST_SESSION_API_STAGE = "12.2"

_SESSION_PATH = re.compile(r"^/v1/sessions/([^/]+)(?:/([^/]+))?$")
_ACTION_TO_OPERATION = {
    "activate": "session.activate",
    "pause": "session.pause",
    "complete": "session.complete",
    "fail": "session.fail",
    "cancel": "session.cancel",
    "resume-state": "session.resume_state",
}


class RestSessionApi:
    """REST route adapter backed by Runtime Session API operations."""

    version = REST_SESSION_API_VERSION
    stage = REST_SESSION_API_STAGE

    def __init__(self, runtime_api: RuntimeApi) -> None:
        self.runtime_api = runtime_api
        self.session_api = attach_session_api(runtime_api)

    def register_routes(self, router: RestRouter) -> None:
        router.add_route("POST", "/v1/sessions", self.create_session)
        router.add_route("GET", "/v1/sessions", self.list_sessions)

    def maybe_dispatch(self, request: RestRequest) -> Optional[RestResponse]:
        match = _SESSION_PATH.match(request.path)
        if not match:
            return None
        session_id, action = match.groups()
        if action is None and request.method == "GET":
            return self.get_session(request, session_id)
        if action in _ACTION_TO_OPERATION:
            if action == "resume-state" and request.method != "GET":
                return RestResponse.error(405, "method not allowed for session resume state", request_id=request.request_id)
            if action != "resume-state" and request.method != "POST":
                return RestResponse.error(405, "method not allowed for session transition", request_id=request.request_id)
            return self.session_action(request, session_id, action)
        return RestResponse.error(404, "REST session route not found", request_id=request.request_id, details={"path": request.path})

    def create_session(self, request: RestRequest) -> RestResponse:
        payload = {
            "name": request.body.get("name"),
            "metadata": dict(request.body.get("metadata") or {}),
        }
        response = self.runtime_api.execute("session.create", payload)
        return self._runtime_response(response, request=request, ok_status=201)

    def list_sessions(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("session.list")
        return self._runtime_response(response, request=request, ok_status=200)

    def get_session(self, request: RestRequest, session_id: str) -> RestResponse:
        response = self.runtime_api.execute("session.get", {"session_id": session_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def session_action(self, request: RestRequest, session_id: str, action: str) -> RestResponse:
        operation = _ACTION_TO_OPERATION[action]
        payload: Dict[str, Any] = {"session_id": session_id}
        if action != "resume-state":
            payload["metadata"] = dict(request.body.get("metadata") or {})
        response = self.runtime_api.execute(operation, payload)
        return self._runtime_response(response, request=request, ok_status=200)

    def _runtime_response(self, response: Any, *, request: RestRequest, ok_status: int) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage, "resource": "session"}
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
                {"method": "POST", "path": "/v1/sessions"},
                {"method": "GET", "path": "/v1/sessions"},
                {"method": "GET", "path": "/v1/sessions/{session_id}"},
                {"method": "POST", "path": "/v1/sessions/{session_id}/activate"},
                {"method": "POST", "path": "/v1/sessions/{session_id}/pause"},
                {"method": "POST", "path": "/v1/sessions/{session_id}/complete"},
                {"method": "POST", "path": "/v1/sessions/{session_id}/fail"},
                {"method": "POST", "path": "/v1/sessions/{session_id}/cancel"},
                {"method": "GET", "path": "/v1/sessions/{session_id}/resume-state"},
            ],
            "runtime_operations": list(self.session_api.operations),
            "uses_frozen_runtime_session_api_only": True,
            "additive_only": True,
        }

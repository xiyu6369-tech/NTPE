"""REST Pipeline API adapter for NTPE 1.0 Beta Stage-12.4.

This module is additive. It exposes HTTP-like pipeline routes while delegating
all pipeline state changes to the frozen Runtime Pipeline API operation surface.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, attach_pipeline_api

from .rest_models import RestRequest, RestResponse
from .rest_router import RestRouter

REST_PIPELINE_API_VERSION = "1.0.0-beta.12.4"
REST_PIPELINE_API_STAGE = "12.4"

_PIPELINE_PATH = re.compile(r"^/v1/pipelines/([^/]+)(?:/([^/]+))?$")
_ACTION_TO_OPERATION = {
    "validate": "pipeline.validate",
    "start": "pipeline.start",
    "pause": "pipeline.pause",
    "resume": "pipeline.resume",
    "complete": "pipeline.complete",
    "fail": "pipeline.fail",
    "cancel": "pipeline.cancel",
    "status": "pipeline.status",
    "summary": "pipeline.summary",
    "stages": "pipeline.add_stage",
}
_READ_ACTIONS = {"status", "summary"}


class RestPipelineApi:
    """REST route adapter backed by Runtime Pipeline API operations."""

    version = REST_PIPELINE_API_VERSION
    stage = REST_PIPELINE_API_STAGE

    def __init__(self, runtime_api: RuntimeApi) -> None:
        self.runtime_api = runtime_api
        self.pipeline_api = attach_pipeline_api(runtime_api)

    def register_routes(self, router: RestRouter) -> None:
        router.add_route("POST", "/v1/pipelines", self.create_pipeline)
        router.add_route("GET", "/v1/pipelines", self.list_pipelines)

    def maybe_dispatch(self, request: RestRequest) -> Optional[RestResponse]:
        match = _PIPELINE_PATH.match(request.path)
        if not match:
            return None
        pipeline_id, action = match.groups()
        if action is None and request.method == "GET":
            return self.get_pipeline(request, pipeline_id)
        if action in _ACTION_TO_OPERATION:
            if action in _READ_ACTIONS and request.method != "GET":
                return RestResponse.error(405, "method not allowed for pipeline read action", request_id=request.request_id)
            if action not in _READ_ACTIONS and request.method != "POST":
                return RestResponse.error(405, "method not allowed for pipeline transition", request_id=request.request_id)
            return self.pipeline_action(request, pipeline_id, action)
        return RestResponse.error(404, "REST pipeline route not found", request_id=request.request_id, details={"path": request.path})

    def create_pipeline(self, request: RestRequest) -> RestResponse:
        payload = {
            "name": request.body.get("name"),
            "stages": tuple(request.body.get("stages") or ()),
            "provider": request.body.get("provider"),
            "workflow_ref": request.body.get("workflow_ref"),
            "metadata": dict(request.body.get("metadata") or {}),
        }
        response = self.runtime_api.execute("pipeline.create", payload)
        return self._runtime_response(response, request=request, ok_status=201)

    def list_pipelines(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("pipeline.list")
        return self._runtime_response(response, request=request, ok_status=200)

    def get_pipeline(self, request: RestRequest, pipeline_id: str) -> RestResponse:
        response = self.runtime_api.execute("pipeline.get", {"pipeline_id": pipeline_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def pipeline_action(self, request: RestRequest, pipeline_id: str, action: str) -> RestResponse:
        operation = _ACTION_TO_OPERATION[action]
        payload: Dict[str, Any] = {"pipeline_id": pipeline_id}
        if action == "stages":
            payload["stage"] = dict(request.body.get("stage") or {})
        elif action not in _READ_ACTIONS:
            payload["metadata"] = dict(request.body.get("metadata") or {})
        if action == "complete":
            payload["result"] = dict(request.body.get("result") or {})
        response = self.runtime_api.execute(operation, payload)
        return self._runtime_response(response, request=request, ok_status=200)

    def _runtime_response(self, response: Any, *, request: RestRequest, ok_status: int) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage, "resource": "pipeline"}
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
                {"method": "POST", "path": "/v1/pipelines"},
                {"method": "GET", "path": "/v1/pipelines"},
                {"method": "GET", "path": "/v1/pipelines/{pipeline_id}"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/stages"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/validate"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/start"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/pause"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/resume"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/complete"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/fail"},
                {"method": "POST", "path": "/v1/pipelines/{pipeline_id}/cancel"},
                {"method": "GET", "path": "/v1/pipelines/{pipeline_id}/status"},
                {"method": "GET", "path": "/v1/pipelines/{pipeline_id}/summary"},
            ],
            "runtime_operations": list(self.pipeline_api.operations),
            "uses_frozen_runtime_pipeline_api_only": True,
            "additive_only": True,
        }

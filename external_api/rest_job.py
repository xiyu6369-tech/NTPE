"""REST Job API adapter for NTPE 1.0 Beta Stage-12.3.

This module is additive. It exposes HTTP-like job routes while delegating
all job state changes to the frozen Runtime Job API operation surface.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from runtime_api import RuntimeApi, attach_job_api

from .rest_models import RestRequest, RestResponse
from .rest_router import RestRouter

REST_JOB_API_VERSION = "1.0.0-beta.12.3"
REST_JOB_API_STAGE = "12.3"

_JOB_PATH = re.compile(r"^/v1/jobs/([^/]+)(?:/([^/]+))?$")
_ACTION_TO_OPERATION = {
    "start": "job.start",
    "pause": "job.pause",
    "resume": "job.resume",
    "stop": "job.stop",
    "cancel": "job.cancel",
    "complete": "job.complete",
    "fail": "job.fail",
    "status": "job.status",
    "result": "job.result",
}
_READ_ACTIONS = {"status", "result"}


class RestJobApi:
    """REST route adapter backed by Runtime Job API operations."""

    version = REST_JOB_API_VERSION
    stage = REST_JOB_API_STAGE

    def __init__(self, runtime_api: RuntimeApi) -> None:
        self.runtime_api = runtime_api
        self.job_api = attach_job_api(runtime_api)

    def register_routes(self, router: RestRouter) -> None:
        router.add_route("POST", "/v1/jobs", self.create_job)
        router.add_route("GET", "/v1/jobs", self.list_jobs)

    def maybe_dispatch(self, request: RestRequest) -> Optional[RestResponse]:
        match = _JOB_PATH.match(request.path)
        if not match:
            return None
        job_id, action = match.groups()
        if action is None and request.method == "GET":
            return self.get_job(request, job_id)
        if action in _ACTION_TO_OPERATION:
            if action in _READ_ACTIONS and request.method != "GET":
                return RestResponse.error(405, "method not allowed for job read action", request_id=request.request_id)
            if action not in _READ_ACTIONS and request.method != "POST":
                return RestResponse.error(405, "method not allowed for job transition", request_id=request.request_id)
            return self.job_action(request, job_id, action)
        return RestResponse.error(404, "REST job route not found", request_id=request.request_id, details={"path": request.path})

    def create_job(self, request: RestRequest) -> RestResponse:
        payload = {
            "session_id": request.body.get("session_id"),
            "name": request.body.get("name"),
            "input_ref": request.body.get("input_ref"),
            "output_ref": request.body.get("output_ref"),
            "provider": request.body.get("provider"),
            "pipeline": request.body.get("pipeline"),
            "metadata": dict(request.body.get("metadata") or {}),
        }
        response = self.runtime_api.execute("job.create", payload)
        return self._runtime_response(response, request=request, ok_status=201)

    def list_jobs(self, request: RestRequest) -> RestResponse:
        response = self.runtime_api.execute("job.list")
        return self._runtime_response(response, request=request, ok_status=200)

    def get_job(self, request: RestRequest, job_id: str) -> RestResponse:
        response = self.runtime_api.execute("job.get", {"job_id": job_id})
        return self._runtime_response(response, request=request, ok_status=200)

    def job_action(self, request: RestRequest, job_id: str, action: str) -> RestResponse:
        operation = _ACTION_TO_OPERATION[action]
        payload: Dict[str, Any] = {"job_id": job_id}
        if action not in _READ_ACTIONS:
            payload["metadata"] = dict(request.body.get("metadata") or {})
        if action == "complete":
            payload["result"] = dict(request.body.get("result") or {})
        response = self.runtime_api.execute(operation, payload)
        return self._runtime_response(response, request=request, ok_status=200)

    def _runtime_response(self, response: Any, *, request: RestRequest, ok_status: int) -> RestResponse:
        body = response.to_dict()
        body["external_api"] = {"version": self.version, "stage": self.stage, "resource": "job"}
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
                {"method": "POST", "path": "/v1/jobs"},
                {"method": "GET", "path": "/v1/jobs"},
                {"method": "GET", "path": "/v1/jobs/{job_id}"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/start"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/pause"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/resume"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/stop"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/cancel"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/complete"},
                {"method": "POST", "path": "/v1/jobs/{job_id}/fail"},
                {"method": "GET", "path": "/v1/jobs/{job_id}/status"},
                {"method": "GET", "path": "/v1/jobs/{job_id}/result"},
            ],
            "runtime_operations": list(self.job_api.operations),
            "uses_frozen_runtime_job_api_only": True,
            "additive_only": True,
        }

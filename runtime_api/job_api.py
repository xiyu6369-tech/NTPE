"""Runtime Job API for NTPE 1.0 Beta Stage-11.3.

The API is additive. It registers job.* operations on the existing RuntimeApi
facade without changing Stage-11.1 Runtime API or Stage-11.2 Session API.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .job_request import RuntimeJobCreateRequest
from .job_response import RuntimeJobListResponse
from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_job import RuntimeJob, RuntimeJobState
from .runtime_request import RuntimeApiRequest


class RuntimeJobApi:
    """Additive job facade that registers job operations on RuntimeApi."""

    operations = (
        "job.create",
        "job.get",
        "job.list",
        "job.start",
        "job.pause",
        "job.resume",
        "job.stop",
        "job.cancel",
        "job.complete",
        "job.fail",
        "job.status",
        "job.result",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._jobs: Dict[str, RuntimeJob] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.runtime_api.register("job.create", self._handle_create)
        self.runtime_api.register("job.get", self._handle_get)
        self.runtime_api.register("job.list", self._handle_list)
        self.runtime_api.register("job.start", self._handle_start)
        self.runtime_api.register("job.pause", self._handle_pause)
        self.runtime_api.register("job.resume", self._handle_resume)
        self.runtime_api.register("job.stop", self._handle_stop)
        self.runtime_api.register("job.cancel", self._handle_cancel)
        self.runtime_api.register("job.complete", self._handle_complete)
        self.runtime_api.register("job.fail", self._handle_fail)
        self.runtime_api.register("job.status", self._handle_status)
        self.runtime_api.register("job.result", self._handle_result)

    def create(self, create_request: RuntimeJobCreateRequest | None = None, **kwargs: Any) -> RuntimeJob:
        request = create_request or RuntimeJobCreateRequest(**kwargs)
        job = RuntimeJob(**request.to_payload())
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> RuntimeJob:
        job = self._jobs.get(str(job_id))
        if job is None:
            raise RuntimeApiNotFoundError("runtime job not found", details={"job_id": str(job_id)})
        return job

    def list(self) -> tuple[RuntimeJob, ...]:
        return tuple(self._jobs.values())

    def transition(
        self,
        job_id: str,
        state: RuntimeJobState | str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> RuntimeJob:
        job = self.get(job_id)
        updated = job.transition(state, metadata=metadata, result=result)
        self._jobs[updated.job_id] = updated
        return updated

    def status(self, job_id: str) -> Dict[str, Any]:
        job = self.get(job_id)
        return {
            "job_id": job.job_id,
            "session_id": job.session_id,
            "state": job.state.value,
            "resumable": job.state in {RuntimeJobState.CREATED, RuntimeJobState.STARTED, RuntimeJobState.PAUSED, RuntimeJobState.STOPPED},
            "metadata": dict(job.metadata),
            "updated_at": job.updated_at,
        }

    def result(self, job_id: str) -> Dict[str, Any]:
        job = self.get(job_id)
        return {
            "job_id": job.job_id,
            "state": job.state.value,
            "available": job.result is not None,
            "result": dict(job.result) if job.result is not None else None,
        }

    def _job_id_from(self, request: RuntimeApiRequest) -> str:
        job_id = request.payload.get("job_id")
        if not job_id:
            raise RuntimeApiValidationError("job_id is required", details={"operation": request.operation})
        return str(job_id)

    def _handle_create(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        create_request = RuntimeJobCreateRequest.from_payload(request.payload)
        return self.create(create_request).to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._job_id_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return RuntimeJobListResponse.from_jobs(self.list()).to_dict()

    def _handle_start(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.STARTED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_pause(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.PAUSED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_resume(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.RESUMED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_stop(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.STOPPED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_cancel(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.CANCELLED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_complete(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(
            self._job_id_from(request),
            RuntimeJobState.COMPLETED,
            metadata=request.payload.get("metadata") or {},
            result=request.payload.get("result") or {},
        ).to_dict()

    def _handle_fail(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._job_id_from(request), RuntimeJobState.FAILED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_status(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.status(self._job_id_from(request))

    def _handle_result(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.result(self._job_id_from(request))


def attach_job_api(runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> RuntimeJobApi:
    return RuntimeJobApi(runtime_api=runtime_api, context=context)

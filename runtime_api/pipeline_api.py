"""Runtime Pipeline API for NTPE 1.0 Beta Stage-11.4.

Registers pipeline.* operations on the existing RuntimeApi facade. This is an
additive API adapter and does not change frozen Workflow internals.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .pipeline_request import RuntimePipelineCreateRequest
from .pipeline_response import RuntimePipelineListResponse
from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_pipeline import RuntimePipeline, RuntimePipelineStage, RuntimePipelineState
from .runtime_request import RuntimeApiRequest


class RuntimePipelineApi:
    """Additive pipeline facade for Runtime API consumers."""

    operations = (
        "pipeline.create",
        "pipeline.get",
        "pipeline.list",
        "pipeline.add_stage",
        "pipeline.validate",
        "pipeline.start",
        "pipeline.pause",
        "pipeline.resume",
        "pipeline.complete",
        "pipeline.fail",
        "pipeline.cancel",
        "pipeline.status",
        "pipeline.summary",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._pipelines: Dict[str, RuntimePipeline] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        for operation in self.operations:
            self.runtime_api.register(operation, getattr(self, f"_handle_{operation.split('.')[1]}"))

    def create(self, create_request: RuntimePipelineCreateRequest | None = None, **kwargs: Any) -> RuntimePipeline:
        request = create_request or RuntimePipelineCreateRequest(**kwargs)
        pipeline = RuntimePipeline(**request.to_payload())
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    def get(self, pipeline_id: str) -> RuntimePipeline:
        pipeline = self._pipelines.get(str(pipeline_id))
        if pipeline is None:
            raise RuntimeApiNotFoundError("runtime pipeline not found", details={"pipeline_id": str(pipeline_id)})
        return pipeline

    def list(self) -> tuple[RuntimePipeline, ...]:
        return tuple(self._pipelines.values())

    def add_stage(self, pipeline_id: str, stage: RuntimePipelineStage) -> RuntimePipeline:
        pipeline = self.get(pipeline_id).with_stage(stage)
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    def transition(
        self,
        pipeline_id: str,
        state: RuntimePipelineState | str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> RuntimePipeline:
        pipeline = self.get(pipeline_id).transition(state, metadata=metadata, result=result)
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    def status(self, pipeline_id: str) -> Dict[str, Any]:
        pipeline = self.get(pipeline_id)
        return {
            "pipeline_id": pipeline.pipeline_id,
            "state": pipeline.state.value,
            "stage_count": len(pipeline.stages),
            "provider": pipeline.provider,
            "workflow_ref": pipeline.workflow_ref,
            "resumable": pipeline.state in {RuntimePipelineState.CREATED, RuntimePipelineState.VALIDATED, RuntimePipelineState.STARTED, RuntimePipelineState.PAUSED},
            "metadata": dict(pipeline.metadata),
            "updated_at": pipeline.updated_at,
        }

    def summary(self, pipeline_id: str) -> Dict[str, Any]:
        pipeline = self.get(pipeline_id)
        return {
            "pipeline_id": pipeline.pipeline_id,
            "name": pipeline.name,
            "state": pipeline.state.value,
            "enabled_stages": [stage.name for stage in pipeline.stages if stage.enabled],
            "disabled_stages": [stage.name for stage in pipeline.stages if not stage.enabled],
            "stage_count": len(pipeline.stages),
            "metadata": dict(pipeline.metadata),
            "result": dict(pipeline.result) if pipeline.result is not None else None,
        }

    def _pipeline_id_from(self, request: RuntimeApiRequest) -> str:
        pipeline_id = request.payload.get("pipeline_id")
        if not pipeline_id:
            raise RuntimeApiValidationError("pipeline_id is required", details={"operation": request.operation})
        return str(pipeline_id)

    def _handle_create(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.create(RuntimePipelineCreateRequest.from_payload(request.payload)).to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._pipeline_id_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return RuntimePipelineListResponse.from_pipelines(self.list()).to_dict()

    def _handle_add_stage(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        stage_payload = request.payload.get("stage") or {}
        if not isinstance(stage_payload, dict):
            raise RuntimeApiValidationError("pipeline stage payload must be a mapping")
        return self.add_stage(self._pipeline_id_from(request), RuntimePipelineStage(**stage_payload)).to_dict()

    def _handle_validate(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        pipeline = self.get(self._pipeline_id_from(request))
        if len(pipeline.stages) == 0:
            raise RuntimeApiValidationError("pipeline must contain at least one stage")
        return self.transition(pipeline.pipeline_id, RuntimePipelineState.VALIDATED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_start(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._pipeline_id_from(request), RuntimePipelineState.STARTED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_pause(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._pipeline_id_from(request), RuntimePipelineState.PAUSED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_resume(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._pipeline_id_from(request), RuntimePipelineState.RESUMED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_complete(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(
            self._pipeline_id_from(request),
            RuntimePipelineState.COMPLETED,
            metadata=request.payload.get("metadata") or {},
            result=request.payload.get("result") or {},
        ).to_dict()

    def _handle_fail(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._pipeline_id_from(request), RuntimePipelineState.FAILED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_cancel(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._pipeline_id_from(request), RuntimePipelineState.CANCELLED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_status(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.status(self._pipeline_id_from(request))

    def _handle_summary(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.summary(self._pipeline_id_from(request))


def attach_pipeline_api(runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> RuntimePipelineApi:
    return RuntimePipelineApi(runtime_api=runtime_api, context=context)

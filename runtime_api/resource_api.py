"""Runtime Resource API for NTPE 1.0 Beta Stage-11.6.

Registers resource.* operations on the existing RuntimeApi facade. The module is
additive and does not modify frozen Platform Services or previous Runtime API
surfaces.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .resource_request import RuntimeResourceCreateRequest
from .resource_response import RuntimeResourceListResponse
from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_request import RuntimeApiRequest
from .runtime_resource import RuntimeResource, RuntimeResourceState, RuntimeResourceType


class RuntimeResourceApi:
    """Additive resource facade for Runtime API consumers."""

    operations = (
        "resource.create",
        "resource.get",
        "resource.list",
        "resource.filter",
        "resource.reserve",
        "resource.attach",
        "resource.release",
        "resource.delete",
        "resource.summary",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._resources: Dict[str, RuntimeResource] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        for operation in self.operations:
            self.runtime_api.register(operation, getattr(self, f"_handle_{operation.split('.')[1]}"))

    def create(self, create_request: RuntimeResourceCreateRequest | None = None, **kwargs: Any) -> RuntimeResource:
        request = create_request or RuntimeResourceCreateRequest(**kwargs)
        resource = RuntimeResource(**request.to_payload())
        self._resources[resource.resource_id] = resource
        return resource

    def get(self, resource_id: str) -> RuntimeResource:
        resource = self._resources.get(str(resource_id))
        if resource is None:
            raise RuntimeApiNotFoundError("runtime resource not found", details={"resource_id": str(resource_id)})
        return resource

    def list(self) -> tuple[RuntimeResource, ...]:
        return tuple(self._resources.values())

    def filter(
        self,
        *,
        resource_type: RuntimeResourceType | str | None = None,
        state: RuntimeResourceState | str | None = None,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
    ) -> tuple[RuntimeResource, ...]:
        resources: Iterable[RuntimeResource] = self._resources.values()
        if resource_type is not None:
            normalized_type = RuntimeResourceType(resource_type)
            resources = [resource for resource in resources if resource.resource_type == normalized_type]
        if state is not None:
            normalized_state = RuntimeResourceState(state)
            resources = [resource for resource in resources if resource.state == normalized_state]
        if owner_id is not None:
            resources = [resource for resource in resources if resource.owner_id == str(owner_id)]
        if session_id is not None:
            resources = [resource for resource in resources if resource.session_id == str(session_id)]
        if job_id is not None:
            resources = [resource for resource in resources if resource.job_id == str(job_id)]
        if pipeline_id is not None:
            resources = [resource for resource in resources if resource.pipeline_id == str(pipeline_id)]
        return tuple(resources)

    def transition(self, resource_id: str, state: RuntimeResourceState | str, *, metadata: Optional[Dict[str, Any]] = None) -> RuntimeResource:
        resource = self.get(resource_id).transition(state, metadata=metadata)
        self._resources[resource.resource_id] = resource
        return resource

    def attach(
        self,
        resource_id: str,
        *,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeResource:
        resource = self.get(resource_id).with_binding(owner_id=owner_id, session_id=session_id, job_id=job_id, pipeline_id=pipeline_id)
        resource = resource.transition(RuntimeResourceState.ATTACHED, metadata=metadata)
        self._resources[resource.resource_id] = resource
        return resource

    def delete(self, resource_id: str, *, metadata: Optional[Dict[str, Any]] = None) -> RuntimeResource:
        return self.transition(resource_id, RuntimeResourceState.DELETED, metadata=metadata)

    def summary(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_state: Dict[str, int] = {}
        total_size = 0
        for resource in self._resources.values():
            by_type[resource.resource_type.value] = by_type.get(resource.resource_type.value, 0) + 1
            by_state[resource.state.value] = by_state.get(resource.state.value, 0) + 1
            total_size += resource.size or 0
        return {
            "count": len(self._resources),
            "by_type": by_type,
            "by_state": by_state,
            "total_size": total_size,
            "resource_ids": list(self._resources.keys()),
        }

    def _resource_id_from(self, request: RuntimeApiRequest) -> str:
        resource_id = request.payload.get("resource_id")
        if not resource_id:
            raise RuntimeApiValidationError("resource_id is required", details={"operation": request.operation})
        return str(resource_id)

    def _handle_create(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.create(RuntimeResourceCreateRequest.from_payload(request.payload)).to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._resource_id_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return RuntimeResourceListResponse.from_resources(self.list()).to_dict()

    def _handle_filter(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        resources = self.filter(
            resource_type=request.payload.get("resource_type"),
            state=request.payload.get("state"),
            owner_id=request.payload.get("owner_id"),
            session_id=request.payload.get("session_id"),
            job_id=request.payload.get("job_id"),
            pipeline_id=request.payload.get("pipeline_id"),
        )
        return RuntimeResourceListResponse.from_resources(resources).to_dict()

    def _handle_reserve(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._resource_id_from(request), RuntimeResourceState.RESERVED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_attach(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.attach(
            self._resource_id_from(request),
            owner_id=request.payload.get("owner_id"),
            session_id=request.payload.get("session_id"),
            job_id=request.payload.get("job_id"),
            pipeline_id=request.payload.get("pipeline_id"),
            metadata=request.payload.get("metadata") or {},
        ).to_dict()

    def _handle_release(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._resource_id_from(request), RuntimeResourceState.RELEASED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_delete(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.delete(self._resource_id_from(request), metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_summary(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.summary()


def attach_resource_api(runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> RuntimeResourceApi:
    return RuntimeResourceApi(runtime_api=runtime_api, context=context)

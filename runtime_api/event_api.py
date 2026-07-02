"""Runtime Event API for NTPE 1.0 Beta Stage-11.5.

Registers event.* operations on the existing RuntimeApi facade. This is an
additive adapter and does not modify frozen Platform Services or Workflow APIs.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .event_request import RuntimeEventPublishRequest
from .event_response import RuntimeEventListResponse
from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_event import RuntimeEvent, RuntimeEventSeverity, RuntimeEventType
from .runtime_request import RuntimeApiRequest


class RuntimeEventApi:
    """Additive event facade for Runtime API consumers."""

    operations = (
        "event.publish",
        "event.get",
        "event.list",
        "event.filter",
        "event.summary",
        "event.clear",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._events: Dict[str, RuntimeEvent] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        for operation in self.operations:
            self.runtime_api.register(operation, getattr(self, f"_handle_{operation.split('.')[1]}"))

    def publish(self, publish_request: RuntimeEventPublishRequest | None = None, **kwargs: Any) -> RuntimeEvent:
        request = publish_request or RuntimeEventPublishRequest(**kwargs)
        event = RuntimeEvent(**request.to_payload())
        self._events[event.event_id] = event
        return event

    def get(self, event_id: str) -> RuntimeEvent:
        event = self._events.get(str(event_id))
        if event is None:
            raise RuntimeApiNotFoundError("runtime event not found", details={"event_id": str(event_id)})
        return event

    def list(self) -> tuple[RuntimeEvent, ...]:
        return tuple(self._events.values())

    def filter(
        self,
        *,
        event_type: RuntimeEventType | str | None = None,
        severity: RuntimeEventSeverity | str | None = None,
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
    ) -> tuple[RuntimeEvent, ...]:
        events: Iterable[RuntimeEvent] = self._events.values()
        if event_type is not None:
            normalized_type = RuntimeEventType(event_type)
            events = [event for event in events if event.event_type == normalized_type]
        if severity is not None:
            normalized_severity = RuntimeEventSeverity(severity)
            events = [event for event in events if event.severity == normalized_severity]
        if session_id is not None:
            events = [event for event in events if event.session_id == str(session_id)]
        if job_id is not None:
            events = [event for event in events if event.job_id == str(job_id)]
        if pipeline_id is not None:
            events = [event for event in events if event.pipeline_id == str(pipeline_id)]
        return tuple(events)

    def clear(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count

    def summary(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for event in self._events.values():
            by_type[event.event_type.value] = by_type.get(event.event_type.value, 0) + 1
            by_severity[event.severity.value] = by_severity.get(event.severity.value, 0) + 1
        return {
            "count": len(self._events),
            "by_type": by_type,
            "by_severity": by_severity,
            "event_ids": list(self._events.keys()),
        }

    def _event_id_from(self, request: RuntimeApiRequest) -> str:
        event_id = request.payload.get("event_id")
        if not event_id:
            raise RuntimeApiValidationError("event_id is required", details={"operation": request.operation})
        return str(event_id)

    def _handle_publish(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.publish(RuntimeEventPublishRequest.from_payload(request.payload)).to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._event_id_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return RuntimeEventListResponse.from_events(self.list()).to_dict()

    def _handle_filter(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        events = self.filter(
            event_type=request.payload.get("event_type"),
            severity=request.payload.get("severity"),
            session_id=request.payload.get("session_id"),
            job_id=request.payload.get("job_id"),
            pipeline_id=request.payload.get("pipeline_id"),
        )
        return RuntimeEventListResponse.from_events(events).to_dict()

    def _handle_summary(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.summary()

    def _handle_clear(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return {"cleared": self.clear()}


def attach_event_api(runtime_api: RuntimeApi) -> RuntimeEventApi:
    return RuntimeEventApi(runtime_api=runtime_api)

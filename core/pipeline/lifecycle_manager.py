"""
NTPE Foundation-05.4 Pipeline Lifecycle Manager

Incremental lifecycle layer for initializing, starting, stopping, completing,
failing, and cleaning scheduled production pipeline executions.  This module is
intentionally additive and consumes Foundation-05.3 schedules without mutating
older contract modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional, Tuple

from core.pipeline.scheduler import (
    PipelineSchedule,
    PipelineScheduleItem,
    SCHEDULE_ITEM_READY,
    normalize_schedule_item,
    schedule_pipeline,
    validate_schedule,
)

LIFECYCLE_CREATED = "created"
LIFECYCLE_INITIALIZED = "initialized"
LIFECYCLE_RUNNING = "running"
LIFECYCLE_STOPPING = "stopping"
LIFECYCLE_STOPPED = "stopped"
LIFECYCLE_COMPLETED = "completed"
LIFECYCLE_FAILED = "failed"
LIFECYCLE_CLEANED = "cleaned"


@dataclass(frozen=True)
class PipelineLifecycleEvent:
    """Auditable lifecycle event emitted by the manager."""

    type: str
    status: str
    timestamp: float = field(default_factory=time)
    stage_id: str = ""
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "status": self.status,
            "timestamp": self.timestamp,
            "stage_id": self.stage_id,
            "message": self.message,
            "metadata": dict(self.metadata or {}),
        }


@dataclass
class PipelineLifecycleState:
    """Mutable lifecycle state used during runtime execution."""

    lifecycle_id: str
    status: str = LIFECYCLE_CREATED
    current_stage_id: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    stopped_at: Optional[float] = None
    cleaned_at: Optional[float] = None
    error: str = ""
    counters: MutableMapping[str, int] = field(default_factory=lambda: {
        "initialized": 0,
        "started": 0,
        "completed": 0,
        "failed": 0,
        "stopped": 0,
        "cleaned": 0,
        "stages_started": 0,
        "stages_completed": 0,
        "stages_failed": 0,
        "stages_skipped": 0,
    })
    events: List[PipelineLifecycleEvent] = field(default_factory=list)
    outputs: MutableMapping[str, Any] = field(default_factory=dict)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def add_event(self, event_type: str, message: str = "", stage_id: str = "", **metadata: Any) -> PipelineLifecycleEvent:
        event = PipelineLifecycleEvent(
            type=event_type,
            status=self.status,
            stage_id=stage_id,
            message=message,
            metadata=metadata,
        )
        self.events.append(event)
        return event

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.lifecycle_state.v1",
            "lifecycle_id": self.lifecycle_id,
            "status": self.status,
            "current_stage_id": self.current_stage_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "stopped_at": self.stopped_at,
            "cleaned_at": self.cleaned_at,
            "error": self.error,
            "counters": dict(self.counters),
            "outputs": dict(self.outputs),
            "metadata": dict(self.metadata),
            "events": [event.to_dict() for event in self.events],
        }


@dataclass(frozen=True)
class PipelineLifecycleResult:
    """Final result object returned by lifecycle execution."""

    status: str
    output: Any = None
    state: Optional[PipelineLifecycleState] = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == LIFECYCLE_COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.lifecycle_result.v1",
            "status": self.status,
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "state": self.state.to_dict() if self.state else None,
        }


def create_lifecycle_state(lifecycle_id: str = "pipeline") -> PipelineLifecycleState:
    state = PipelineLifecycleState(lifecycle_id=str(lifecycle_id or "pipeline"))
    state.add_event("lifecycle_created")
    return state


def validate_lifecycle_state(state: PipelineLifecycleState) -> bool:
    if not isinstance(state, PipelineLifecycleState):
        raise TypeError("state must be PipelineLifecycleState")
    if not state.lifecycle_id:
        raise ValueError("lifecycle_id is required")
    if state.status not in {
        LIFECYCLE_CREATED,
        LIFECYCLE_INITIALIZED,
        LIFECYCLE_RUNNING,
        LIFECYCLE_STOPPING,
        LIFECYCLE_STOPPED,
        LIFECYCLE_COMPLETED,
        LIFECYCLE_FAILED,
        LIFECYCLE_CLEANED,
    }:
        raise ValueError(f"invalid lifecycle status: {state.status}")
    return True


def normalize_lifecycle_event(event: Any) -> PipelineLifecycleEvent:
    if isinstance(event, PipelineLifecycleEvent):
        return event
    if isinstance(event, str):
        return PipelineLifecycleEvent(type=event, status=LIFECYCLE_CREATED)
    if isinstance(event, Mapping):
        return PipelineLifecycleEvent(
            type=str(event.get("type") or event.get("event") or "lifecycle_event"),
            status=str(event.get("status") or LIFECYCLE_CREATED),
            timestamp=float(event.get("timestamp") or time()),
            stage_id=str(event.get("stage_id") or ""),
            message=str(event.get("message") or ""),
            metadata=dict(event.get("metadata") or {}),
        )
    raise TypeError("unsupported lifecycle event")


class PipelineLifecycleManager:
    """Execute scheduled stages through a stable lifecycle contract."""

    def __init__(self, schedule: PipelineSchedule, lifecycle_id: str = "pipeline") -> None:
        validate_schedule(schedule)
        self.schedule = schedule
        self.state = create_lifecycle_state(lifecycle_id)
        self.stop_requested = False

    def initialize(self, payload: Optional[Any] = None, **metadata: Any) -> PipelineLifecycleState:
        self.state.status = LIFECYCLE_INITIALIZED
        self.state.metadata.update(metadata)
        if payload is not None:
            self.state.metadata["payload"] = payload
        self.state.counters["initialized"] += 1
        self.state.add_event("lifecycle_initialized", schedule_count=len(self.schedule.items))
        return self.state

    def start(self, payload: Optional[Any] = None) -> PipelineLifecycleResult:
        if self.state.status == LIFECYCLE_CREATED:
            self.initialize(payload=payload)
        self.state.status = LIFECYCLE_RUNNING
        self.state.started_at = self.state.started_at or time()
        self.state.counters["started"] += 1
        self.state.add_event("lifecycle_started")

        current: Any = payload
        try:
            for item in self.schedule.items:
                if item.status != SCHEDULE_ITEM_READY:
                    self.state.counters["stages_skipped"] += 1
                    self.state.add_event("stage_skipped", stage_id=item.stage_id, reason=item.reason, item_status=item.status)
                    continue

                if self.stop_requested:
                    return self.stop("stop requested before stage", output=current)

                current = self._execute_stage(item, current)

            self.state.status = LIFECYCLE_COMPLETED
            self.state.completed_at = time()
            self.state.current_stage_id = ""
            self.state.outputs["final"] = current
            self.state.counters["completed"] += 1
            self.state.add_event("lifecycle_completed")
            return PipelineLifecycleResult(status=LIFECYCLE_COMPLETED, output=current, state=self.state)
        except Exception as exc:
            return self.fail(exc)

    def _execute_stage(self, item: PipelineScheduleItem, value: Any) -> Any:
        self.state.current_stage_id = item.stage_id
        self.state.counters["stages_started"] += 1
        self.state.add_event("stage_started", stage_id=item.stage_id)

        output = value
        handler: Optional[Callable[[Any], Any]] = item.stage.handler if item.stage is not None else None
        if handler is not None:
            output = handler(value)

        self.state.outputs[item.stage_id] = output
        self.state.counters["stages_completed"] += 1
        self.state.add_event("stage_completed", stage_id=item.stage_id)
        return output

    def request_stop(self, reason: str = "") -> PipelineLifecycleState:
        self.stop_requested = True
        self.state.status = LIFECYCLE_STOPPING
        self.state.add_event("lifecycle_stop_requested", message=reason)
        return self.state

    def stop(self, reason: str = "", output: Any = None) -> PipelineLifecycleResult:
        self.state.status = LIFECYCLE_STOPPED
        self.state.stopped_at = time()
        self.state.counters["stopped"] += 1
        self.state.outputs["final"] = output
        self.state.add_event("lifecycle_stopped", message=reason)
        return PipelineLifecycleResult(status=LIFECYCLE_STOPPED, output=output, state=self.state)

    def fail(self, error: Any) -> PipelineLifecycleResult:
        self.state.status = LIFECYCLE_FAILED
        self.state.completed_at = time()
        self.state.error = str(error)
        self.state.counters["failed"] += 1
        self.state.counters["stages_failed"] += 1
        self.state.add_event("lifecycle_failed", message=str(error), stage_id=self.state.current_stage_id)
        return PipelineLifecycleResult(status=LIFECYCLE_FAILED, output=None, state=self.state, error=str(error))

    def cleanup(self) -> PipelineLifecycleState:
        self.state.status = LIFECYCLE_CLEANED
        self.state.cleaned_at = time()
        self.state.counters["cleaned"] += 1
        self.state.add_event("lifecycle_cleaned")
        return self.state

    def export_manifest(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.lifecycle_manager.v1",
            "schedule": self.schedule.to_dict(),
            "state": self.state.to_dict(),
        }


def create_lifecycle_manager(schedule_or_registry: Any, lifecycle_id: str = "pipeline") -> PipelineLifecycleManager:
    if isinstance(schedule_or_registry, PipelineSchedule):
        schedule = schedule_or_registry
    else:
        schedule = schedule_pipeline(schedule_or_registry, strict=True)
    return PipelineLifecycleManager(schedule, lifecycle_id=lifecycle_id)


def run_pipeline_lifecycle(schedule_or_registry: Any, payload: Any = None, lifecycle_id: str = "pipeline") -> PipelineLifecycleResult:
    manager = create_lifecycle_manager(schedule_or_registry, lifecycle_id=lifecycle_id)
    manager.initialize(payload=payload)
    return manager.start(payload=payload)

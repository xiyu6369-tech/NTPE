# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

WORKFLOW_STARTED = "WorkflowStarted"
WORKFLOW_STEP_STARTED = "WorkflowStepStarted"
WORKFLOW_STEP_COMPLETED = "WorkflowStepCompleted"
WORKFLOW_FAILED = "WorkflowFailed"
WORKFLOW_COMPLETED = "WorkflowCompleted"


@dataclass(frozen=True)
class WorkflowEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class WorkflowEventBus:
    def __init__(self) -> None:
        self.events: List[WorkflowEvent] = []
        self._subscribers: List[Callable[[WorkflowEvent], None]] = []

    def subscribe(self, callback: Callable[[WorkflowEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, **payload: Any) -> WorkflowEvent:
        event = WorkflowEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for callback in self._subscribers:
            callback(event)
        return event

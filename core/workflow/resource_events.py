# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

RESOURCE_OPTIMIZATION_STARTED = "ResourceOptimizationStarted"
RESOURCE_OPTIMIZATION_COMPLETED = "ResourceOptimizationCompleted"
RESOURCE_BUDGET_WARNING = "ResourceBudgetWarning"


@dataclass(frozen=True)
class ResourceEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class ResourceEventBus:
    def __init__(self) -> None:
        self.events: List[ResourceEvent] = []
        self._subscribers: List[Callable[[ResourceEvent], None]] = []

    def subscribe(self, callback: Callable[[ResourceEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, **payload: Any) -> ResourceEvent:
        event = ResourceEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)
        return event

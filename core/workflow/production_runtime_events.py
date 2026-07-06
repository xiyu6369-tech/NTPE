# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

PRODUCTION_RUNTIME_STARTED = "ProductionRuntimeStarted"
PRODUCTION_RUNTIME_COMPLETED = "ProductionRuntimeCompleted"
PRODUCTION_RUNTIME_FAILED = "ProductionRuntimeFailed"
PRODUCTION_RUNTIME_COMPONENT_BOUND = "ProductionRuntimeComponentBound"


@dataclass(frozen=True)
class ProductionRuntimeEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class ProductionRuntimeEventBus:
    def __init__(self) -> None:
        self.events: List[ProductionRuntimeEvent] = []
        self._subscribers: List[Callable[[ProductionRuntimeEvent], None]] = []

    def subscribe(self, callback: Callable[[ProductionRuntimeEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, **payload: Any) -> ProductionRuntimeEvent:
        event = ProductionRuntimeEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)
        return event

    def to_list(self) -> List[Dict[str, Any]]:
        return [{"name": event.name, "payload": dict(event.payload)} for event in self.events]

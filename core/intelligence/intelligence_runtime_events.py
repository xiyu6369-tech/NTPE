# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

INTELLIGENCE_RUNTIME_STARTED = "IntelligenceRuntimeStarted"
INTELLIGENCE_RUNTIME_STEP_COMPLETED = "IntelligenceRuntimeStepCompleted"
INTELLIGENCE_RUNTIME_COMPLETED = "IntelligenceRuntimeCompleted"


@dataclass(frozen=True)
class IntelligenceRuntimeEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class IntelligenceRuntimeEventBus:
    def __init__(self) -> None:
        self._subscribers: List[Callable[[IntelligenceRuntimeEvent], None]] = []
        self.events: List[IntelligenceRuntimeEvent] = []

    def subscribe(self, subscriber: Callable[[IntelligenceRuntimeEvent], None]) -> None:
        self._subscribers.append(subscriber)

    def emit(self, name: str, **payload: Any) -> IntelligenceRuntimeEvent:
        event = IntelligenceRuntimeEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for subscriber in list(self._subscribers):
            subscriber(event)
        return event

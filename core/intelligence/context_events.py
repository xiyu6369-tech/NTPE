# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

CONTEXT_STARTED = "ContextStarted"
CONTEXT_COMPLETED = "ContextCompleted"
CONTEXT_COMPRESSED = "ContextCompressed"


@dataclass(frozen=True)
class ContextEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class ContextEventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[ContextEvent], None]]] = {}
        self.events: List[ContextEvent] = []

    def subscribe(self, name: str, handler: Callable[[ContextEvent], None]) -> None:
        self._subscribers.setdefault(name, []).append(handler)

    def emit(self, name: str, **payload: Any) -> ContextEvent:
        event = ContextEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for handler in self._subscribers.get(name, []):
            handler(event)
        return event

# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

SEMANTIC_STARTED = "SemanticStarted"
SEMANTIC_ANALYZED = "SemanticAnalyzed"
SEMANTIC_COMPLETED = "SemanticCompleted"


@dataclass(frozen=True)
class SemanticEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class SemanticEventBus:
    def __init__(self) -> None:
        self.events: List[SemanticEvent] = []
        self._listeners: List[Callable[[SemanticEvent], None]] = []

    def subscribe(self, listener: Callable[[SemanticEvent], None]) -> None:
        self._listeners.append(listener)

    def emit(self, name: str, **payload: Any) -> SemanticEvent:
        event = SemanticEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for listener in list(self._listeners):
            listener(event)
        return event

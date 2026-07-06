# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

NARRATIVE_STARTED = "NarrativeStarted"
NARRATIVE_ANALYZED = "NarrativeAnalyzed"
NARRATIVE_COMPLETED = "NarrativeCompleted"


@dataclass(frozen=True)
class NarrativeEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class NarrativeEventBus:
    """Small in-process event bus kept deterministic for runtime and tests."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[NarrativeEvent], None]]] = {}
        self.events: List[NarrativeEvent] = []

    def subscribe(self, name: str, handler: Callable[[NarrativeEvent], None]) -> None:
        self._subscribers.setdefault(name, []).append(handler)

    def emit(self, name: str, **payload: Any) -> NarrativeEvent:
        event = NarrativeEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for handler in self._subscribers.get(name, []):
            handler(event)
        return event

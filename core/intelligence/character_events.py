# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

CHARACTER_STARTED = "CharacterStarted"
CHARACTER_ANALYZED = "CharacterAnalyzed"
CHARACTER_COMPLETED = "CharacterCompleted"


@dataclass(frozen=True)
class CharacterEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class CharacterEventBus:
    def __init__(self) -> None:
        self.events: List[CharacterEvent] = []
        self._subscribers: List[Callable[[CharacterEvent], None]] = []

    def subscribe(self, callback: Callable[[CharacterEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, **payload: Any) -> CharacterEvent:
        event = CharacterEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for callback in self._subscribers:
            callback(event)
        return event

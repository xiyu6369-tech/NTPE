# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

MEMORY_STARTED = "translation_memory.started"
MEMORY_ENTRY_ADDED = "translation_memory.entry_added"
MEMORY_MATCHED = "translation_memory.matched"
MEMORY_COMPLETED = "translation_memory.completed"


@dataclass(frozen=True)
class TranslationMemoryEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class TranslationMemoryEventBus:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[TranslationMemoryEvent], None]]] = {}
        self.events: List[TranslationMemoryEvent] = []

    def subscribe(self, name: str, listener: Callable[[TranslationMemoryEvent], None]) -> None:
        self._listeners.setdefault(name, []).append(listener)

    def emit(self, name: str, **payload: Any) -> TranslationMemoryEvent:
        event = TranslationMemoryEvent(name=name, payload=dict(payload))
        self.events.append(event)
        for listener in self._listeners.get(name, []):
            listener(event)
        return event

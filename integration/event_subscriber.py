"""Event subscriber helpers for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from typing import Any, Optional


class EventSubscriber:
    def __init__(self, callback: Any, *, name: Optional[str] = None, topic: Optional[str] = None, event_type: Optional[str] = None, source: Optional[str] = None, priority: int = 0) -> None:
        self.callback = callback
        self.name = name
        self.topic = topic
        self.event_type = event_type
        self.source = source
        self.priority = priority

    def register(self, bus: Any) -> str:
        return bus.subscribe(self.callback, name=self.name, topic=self.topic, event_type=self.event_type, source=self.source, priority=self.priority)

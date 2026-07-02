"""Event publisher for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .event_models import Event


class EventPublisher:
    def __init__(self, bus: Any, *, source: str = "integration", topic: str = "default") -> None:
        self.bus = bus
        self.source = source
        self.topic = topic

    def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None, *, topic: Optional[str] = None, priority: int = 0, **metadata: Any):
        event = Event(type=event_type, payload=dict(payload or {}), source=self.source, topic=topic or self.topic, priority=priority, metadata=dict(metadata))
        return self.bus.publish(event)

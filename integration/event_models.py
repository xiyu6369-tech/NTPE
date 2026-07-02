"""Event models for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, Optional
from uuid import uuid4

EVENT_BUS_VERSION = "0.8.5"
EVENT_BUS_STAGE = "Stage-08.5 Event Bus"


@dataclass
class Event:
    """Stable event envelope shared by runtime, CLI, SDK, plugin and extension layers."""

    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "integration"
    topic: str = "default"
    priority: int = 0
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: float = field(default_factory=time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "topic": self.topic,
            "source": self.source,
            "priority": self.priority,
            "payload": dict(self.payload),
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass
class EventSubscription:
    name: str
    callback: Any
    topic: Optional[str] = None
    event_type: Optional[str] = None
    source: Optional[str] = None
    priority: int = 0
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, event: Event) -> bool:
        if not self.active:
            return False
        if self.topic is not None and self.topic != event.topic:
            return False
        if self.event_type is not None and self.event_type != event.type:
            return False
        if self.source is not None and self.source != event.source:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "topic": self.topic,
            "event_type": self.event_type,
            "source": self.source,
            "priority": self.priority,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


@dataclass
class EventDispatchResult:
    ok: bool
    event: Event
    delivered: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "event": self.event.to_dict(),
            "delivered": self.delivered,
            "errors": list(self.errors),
        }

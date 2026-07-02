"""SDK-CLI bridge event model for NTPE Stage-08.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

BRIDGE_EVENT_REGISTERED = "bridge.registered"
BRIDGE_EVENT_COMMAND = "bridge.command"
BRIDGE_EVENT_COMPLETED = "bridge.completed"
BRIDGE_EVENT_FAILED = "bridge.failed"


@dataclass
class BridgeEvent:
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    surface: str = "bridge"
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "surface": self.surface,
            "correlation_id": self.correlation_id,
            "payload": dict(self.payload),
        }


class BridgeEventBus:
    version = "0.8.2"

    def __init__(self) -> None:
        self.events: List[BridgeEvent] = []
        self._subscribers: List[Callable[[BridgeEvent], None]] = []

    def subscribe(self, callback: Callable[[BridgeEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event_type: str, *, surface: str = "bridge", payload: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> BridgeEvent:
        event = BridgeEvent(event_type=event_type, surface=surface, payload=dict(payload or {}), correlation_id=correlation_id)
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)
        return event

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self.events), "events": [event.to_dict() for event in self.events]}

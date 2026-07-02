"""Extension framework event bus for NTPE Stage-08.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

EXTENSION_EVENT_REGISTERED = "extension.registered"
EXTENSION_EVENT_LOADED = "extension.loaded"
EXTENSION_EVENT_INITIALIZED = "extension.initialized"
EXTENSION_EVENT_ENABLED = "extension.enabled"
EXTENSION_EVENT_DISABLED = "extension.disabled"
EXTENSION_EVENT_EXECUTED = "extension.executed"
EXTENSION_EVENT_UNLOADED = "extension.unloaded"
EXTENSION_EVENT_DISCOVERED = "extension.discovered"
EXTENSION_EVENT_FAILED = "extension.failed"


@dataclass
class ExtensionEvent:
    event_type: str
    extension_name: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "integration"
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "extension_name": self.extension_name,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "payload": dict(self.payload),
        }


class ExtensionEventBus:
    version = "0.8.4"

    def __init__(self) -> None:
        self.events: List[ExtensionEvent] = []
        self._subscribers: List[Callable[[ExtensionEvent], None]] = []

    def subscribe(self, callback: Callable[[ExtensionEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event_type: str, *, extension_name: Optional[str] = None, payload: Optional[Dict[str, Any]] = None, source: str = "integration", correlation_id: Optional[str] = None) -> ExtensionEvent:
        event = ExtensionEvent(event_type=event_type, extension_name=extension_name, payload=dict(payload or {}), source=source, correlation_id=correlation_id)
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)
        return event

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self.events), "events": [event.to_dict() for event in self.events]}

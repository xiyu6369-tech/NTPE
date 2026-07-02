"""Plugin integration event bus for NTPE Stage-08.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

PLUGIN_EVENT_REGISTERED = "plugin.integration.registered"
PLUGIN_EVENT_LOADED = "plugin.integration.loaded"
PLUGIN_EVENT_INITIALIZED = "plugin.integration.initialized"
PLUGIN_EVENT_EXECUTED = "plugin.integration.executed"
PLUGIN_EVENT_UNLOADED = "plugin.integration.unloaded"
PLUGIN_EVENT_FAILED = "plugin.integration.failed"
PLUGIN_EVENT_DISCOVERED = "plugin.integration.discovered"


@dataclass
class PluginIntegrationEvent:
    event_type: str
    plugin_name: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "integration"
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "plugin_name": self.plugin_name,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "payload": dict(self.payload),
        }


class PluginEventBus:
    version = "0.8.3"

    def __init__(self) -> None:
        self.events: List[PluginIntegrationEvent] = []
        self._subscribers: List[Callable[[PluginIntegrationEvent], None]] = []

    def subscribe(self, callback: Callable[[PluginIntegrationEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event_type: str, *, plugin_name: Optional[str] = None, payload: Optional[Dict[str, Any]] = None, source: str = "integration", correlation_id: Optional[str] = None) -> PluginIntegrationEvent:
        event = PluginIntegrationEvent(event_type=event_type, plugin_name=plugin_name, payload=dict(payload or {}), source=source, correlation_id=correlation_id)
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)
        return event

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self.events), "events": [event.to_dict() for event in self.events]}

"""Foundation-07.5 event dispatcher."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .event import IntelligenceEvent
from .event_bus import IntelligenceEventBus


class IntelligenceEventDispatcher:
    """Routes event dictionaries or event instances through a shared bus."""

    version = "foundation-07.5"

    def __init__(self, bus: Optional[IntelligenceEventBus] = None) -> None:
        self.bus = bus or IntelligenceEventBus()

    def dispatch(self, event: IntelligenceEvent | Dict[str, Any] | str, payload: Optional[Dict[str, Any]] = None, **kwargs: Any) -> IntelligenceEvent:
        return self.bus.publish(event, payload=payload, **kwargs)

    def route_runtime_event(self, event_type: str, segment_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.dispatch(event_type, payload=payload or {}, source="runtime", segment_id=segment_id)

    def route_lifecycle_event(self, event_type: str, scope_key: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.dispatch(event_type, payload=payload or {}, source="lifecycle", scope_key=scope_key)

    def route_persistence_event(self, event_type: str, scope_key: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.dispatch(event_type, payload=payload or {}, source="persistence", scope_key=scope_key)

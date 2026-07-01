"""Foundation-07.5 publisher helper."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .event import IntelligenceEvent
from .event_bus import IntelligenceEventBus


class IntelligencePublisher:
    """Convenience wrapper around IntelligenceEventBus.publish."""

    def __init__(self, bus: Optional[IntelligenceEventBus] = None, source: str = "intelligence") -> None:
        self.bus = bus or IntelligenceEventBus()
        self.source = source

    def publish(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        scope_key: Optional[str] = None,
        segment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IntelligenceEvent:
        return self.bus.publish(
            event_type,
            payload=payload or {},
            source=self.source,
            scope_key=scope_key,
            segment_id=segment_id,
            metadata=metadata or {},
        )

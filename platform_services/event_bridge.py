"""Platform event bridge helpers for NTPE 1.0 Beta Stage-10.5."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .event_bus import PlatformEventBus


class PlatformEventBridge:
    """Small adapter that lets services emit events without owning the bus."""

    version = "1.0.0-beta.10.5"
    stage = "10.5"

    def __init__(self, event_bus: Optional[PlatformEventBus] = None, *, source: str = "platform.bridge", metadata: Optional[Dict[str, Any]] = None) -> None:
        self.event_bus = event_bus or PlatformEventBus(metadata={"created_by": "event_bridge"})
        self.source = str(source)
        self.metadata = dict(metadata or {})

    def emit(self, event_type: str, payload: Any = None, *, topic: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        merged = {**self.metadata, **dict(metadata or {})}
        return self.event_bus.publish(event_type, payload, source=self.source, topic=topic, metadata=merged)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "source": self.source,
            "event_bus": self.event_bus.summary(),
            "additive_only": True,
            "metadata": dict(self.metadata),
        }


def create_event_bridge(event_bus: Optional[PlatformEventBus] = None, **kwargs: Any) -> PlatformEventBridge:
    return PlatformEventBridge(event_bus, **kwargs)

"""NTPE 1.0 Beta Stage-01 Production Runtime telemetry."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuntimeTelemetryEvent:
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    level: str = "info"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "level": self.level,
            "timestamp": self.timestamp,
        }


class RuntimeTelemetry:
    """In-process telemetry collector with optional bridge to Event Bus."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self, event_bus: Any = None, keep_history: bool = True, max_history: int = 1000):
        self.event_bus = event_bus
        self.keep_history = keep_history
        self.max_history = max(1, int(max_history))
        self._events: List[RuntimeTelemetryEvent] = []

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None, level: str = "info") -> RuntimeTelemetryEvent:
        event = RuntimeTelemetryEvent(event_type=str(event_type), payload=dict(payload or {}), level=str(level or "info"))
        if self.keep_history:
            self._events.append(event)
            if len(self._events) > self.max_history:
                self._events = self._events[-self.max_history:]
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            try:
                self.event_bus.publish(event.event_type, event.to_dict())
            except TypeError:
                self.event_bus.publish(event.to_dict())
        return event

    def history(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        data = [event.to_dict() for event in self._events]
        if event_type is None:
            return data
        return [item for item in data if item.get("event_type") == event_type]

    def clear(self) -> None:
        self._events.clear()

    def manifest(self) -> Dict[str, Any]:
        return {"name": "production_runtime_telemetry", "version": self.version, "event_count": len(self._events)}


__all__ = ["RuntimeTelemetry", "RuntimeTelemetryEvent"]

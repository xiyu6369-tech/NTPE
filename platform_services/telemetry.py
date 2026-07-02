"""Platform telemetry event model for NTPE 1.0 Beta Stage-10.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Tuple
from uuid import uuid4

PLATFORM_TELEMETRY_VERSION = "1.0.0-beta.10.4"
PLATFORM_TELEMETRY_STAGE = "10.4"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class PlatformTelemetryEvent:
    """Append-only telemetry event for platform services."""

    event_type: str
    source: str = "platform"
    message: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    event_id: str = field(default_factory=lambda: f"platform-telemetry-{uuid4().hex[:12]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = PLATFORM_TELEMETRY_VERSION
    stage = PLATFORM_TELEMETRY_STAGE

    def __post_init__(self) -> None:
        if not self.event_type or not str(self.event_type).strip():
            raise ValueError("telemetry event_type is required")
        object.__setattr__(self, "event_type", str(self.event_type))
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


class PlatformTelemetryBuffer:
    """Small in-memory telemetry buffer with snapshot-friendly export."""

    version = PLATFORM_TELEMETRY_VERSION
    stage = PLATFORM_TELEMETRY_STAGE

    def __init__(self, *, max_events: int = 1000) -> None:
        self.max_events = int(max_events)
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")
        self._events: list[PlatformTelemetryEvent] = []

    def record(self, event_type: str, *, source: str = "platform", message: str = "", metadata: Dict[str, Any] | None = None) -> PlatformTelemetryEvent:
        event = PlatformTelemetryEvent(event_type=event_type, source=source, message=message, metadata=dict(metadata or {}))
        self._events.append(event)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]
        return event

    def events(self) -> Tuple[PlatformTelemetryEvent, ...]:
        return tuple(self._events)

    def latest(self, limit: int | None = None) -> Tuple[PlatformTelemetryEvent, ...]:
        if limit is None:
            return self.events()
        return tuple(self._events[-int(limit):])

    def extend(self, events: Iterable[PlatformTelemetryEvent]) -> "PlatformTelemetryBuffer":
        for event in events:
            if not isinstance(event, PlatformTelemetryEvent):
                raise TypeError("telemetry buffer accepts PlatformTelemetryEvent only")
            self._events.append(event)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]
        return self

    def summary(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for event in self._events:
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
        return {
            "version": self.version,
            "stage": self.stage,
            "count": len(self._events),
            "by_type": by_type,
        }

    def report(self) -> Dict[str, Any]:
        payload = self.summary()
        payload["events"] = [event.to_dict() for event in self._events]
        payload["additive_only"] = True
        return payload

"""Runtime Event API response helpers for NTPE 1.0 Beta Stage-11.5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from .runtime_event import RuntimeEvent

RUNTIME_EVENT_RESPONSE_VERSION = "1.0.0-beta.11.5"
RUNTIME_EVENT_RESPONSE_STAGE = "11.5"


@dataclass(frozen=True)
class RuntimeEventListResponse:
    """Serializable event-list response."""

    events: tuple[RuntimeEvent, ...] = field(default_factory=tuple)

    version = RUNTIME_EVENT_RESPONSE_VERSION
    stage = RUNTIME_EVENT_RESPONSE_STAGE

    @classmethod
    def from_events(cls, events: Iterable[RuntimeEvent]) -> "RuntimeEventListResponse":
        return cls(events=tuple(events))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "events": [event.to_dict() for event in self.events],
            "count": len(self.events),
        }

"""Runtime event bridge for NTPE Stage-08.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import time

RUNTIME_EVENT_CREATED = "runtime.created"
RUNTIME_EVENT_STARTED = "runtime.started"
RUNTIME_EVENT_COMPLETED = "runtime.completed"
RUNTIME_EVENT_FAILED = "runtime.failed"
RUNTIME_EVENT_DISPOSED = "runtime.disposed"
RUNTIME_EVENT_RESUMED = "runtime.resumed"
RUNTIME_EVENT_STOPPED = "runtime.stopped"


@dataclass
class RuntimeEvent:
    event_type: str
    runtime_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.event_type, "runtime_id": self.runtime_id, "payload": dict(self.payload), "created_at": self.created_at}


class RuntimeEventBridge:
    """Small synchronous event bus used by runtime integration tests and adapters."""

    def __init__(self) -> None:
        self.events: List[RuntimeEvent] = []
        self._callbacks: List[Callable[[RuntimeEvent], None]] = []

    def subscribe(self, callback: Callable[[RuntimeEvent], None]) -> Callable[[RuntimeEvent], None]:
        self._callbacks.append(callback)
        return callback

    def emit(self, event_type: str, *, runtime_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> RuntimeEvent:
        event = RuntimeEvent(event_type=event_type, runtime_id=runtime_id, payload=dict(payload or {}))
        self.events.append(event)
        for callback in tuple(self._callbacks):
            callback(event)
        return event

    def manifest(self) -> Dict[str, Any]:
        return {"count": len(self.events), "events": [event.to_dict() for event in self.events]}

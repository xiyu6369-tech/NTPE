# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

EXPORT_STARTED = "export_started"
EXPORT_COMPLETED = "export_completed"
EXPORT_FAILED = "export_failed"


@dataclass
class ExportEvent:
    name: str
    format: str
    payload: Dict[str, Any] = field(default_factory=dict)


class ExportEventBus:
    def __init__(self) -> None:
        self._subscribers: List[Callable[[ExportEvent], None]] = []
        self.events: List[ExportEvent] = []

    def subscribe(self, callback: Callable[[ExportEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event: ExportEvent) -> None:
        self.events.append(event)
        for callback in list(self._subscribers):
            callback(event)

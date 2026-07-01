"""Foundation-07.5 subscriber helpers."""

from __future__ import annotations

from typing import Any, Callable, List

from .event import IntelligenceEvent
from .event_bus import IntelligenceEventBus


class IntelligenceSubscriber:
    """Callable subscriber that records received events and delegates optionally."""

    def __init__(self, handler: Callable[[IntelligenceEvent], Any] | None = None) -> None:
        self.handler = handler
        self.received: List[IntelligenceEvent] = []

    def __call__(self, event: IntelligenceEvent) -> Any:
        self.received.append(event)
        if self.handler is not None:
            return self.handler(event)
        return None

    def subscribe_to(self, bus: IntelligenceEventBus, event_type: str = "*") -> "IntelligenceSubscriber":
        bus.subscribe(event_type, self)
        return self

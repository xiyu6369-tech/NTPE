from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List

from .telemetry_events import ProviderTelemetryEvent

TelemetrySubscriber = Callable[[ProviderTelemetryEvent], None]


@dataclass
class ProviderTelemetrySink:
    """In-memory telemetry sink with optional subscribers.

    The sink is dependency-free so it can be used by CLI, tests, runtime, Web UI,
    and future exporters without forcing a vendor-specific observability stack.
    """

    events: List[ProviderTelemetryEvent] = field(default_factory=list)
    subscribers: List[TelemetrySubscriber] = field(default_factory=list)
    max_events: int = 1000

    def emit(self, event: ProviderTelemetryEvent) -> None:
        self.events.append(event)
        if self.max_events > 0 and len(self.events) > self.max_events:
            del self.events[0 : len(self.events) - self.max_events]
        for subscriber in list(self.subscribers):
            subscriber(event)

    def subscribe(self, subscriber: TelemetrySubscriber) -> None:
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def snapshot(self) -> List[dict]:
        return [event.to_dict() for event in self.events]

    def filter(self, event_type: str | None = None, provider: str | None = None) -> Iterable[ProviderTelemetryEvent]:
        for event in self.events:
            if event_type is not None and event.event_type != event_type:
                continue
            if provider is not None and event.provider != provider:
                continue
            yield event

    def clear(self) -> None:
        self.events.clear()

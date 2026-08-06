"""RM-6.3.3 Runtime Trace Timeline.

Ordered, immutable container for TraceEvent records. Provides
filtered iteration and deterministic replay of a session's
execution trace. No provider imports. No network calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from .models import TraceEvent, EventType


@dataclass(frozen=True)
class RuntimeTimeline:
    """Ordered sequence of immutable TraceEvent records for a session.

    Events are stored in insertion order. All query methods return
    copies or iterators — the underlying list is immutable after
    construction.

    Timeline is deterministic: iterating the same timeline repeatedly
    produces the same events in the same order.
    """

    session_id: str = ""
    events: List[TraceEvent] = field(default_factory=list)

    version: str = "rm-6.3.3"

    @property
    def event_count(self) -> int:
        return len(self.events)

    def append_event(self, event: TraceEvent) -> RuntimeTimeline:
        """Return a new RuntimeTimeline with the event appended."""
        return RuntimeTimeline(
            session_id=self.session_id,
            events=list(self.events) + [event],
        )

    def events_for_chunk(self, chunk_index: int) -> List[TraceEvent]:
        """Return all events associated with a specific chunk index."""
        return [e for e in self.events if e.chunk_index == chunk_index]

    def events_for_session(self, session_id: str) -> List[TraceEvent]:
        """Return all events associated with a specific session."""
        return [e for e in self.events if e.session_id == session_id]

    def events_by_type(self, event_type: EventType) -> List[TraceEvent]:
        """Return all events of a given EventType in chronological order."""
        return [e for e in self.events if e.event_type == event_type]

    def latest_event(self) -> Optional[TraceEvent]:
        """Return the most recent event, or ``None`` if the timeline is empty."""
        return self.events[-1] if self.events else None

    def first_event(self) -> Optional[TraceEvent]:
        """Return the first event, or ``None`` if the timeline is empty."""
        return self.events[0] if self.events else None

    def retry_events(self) -> List[TraceEvent]:
        """Return all retry events in chronological order."""
        return self.events_by_type(EventType.RETRY_STARTED) + self.events_by_type(EventType.RETRY_COMPLETED)

    def error_events(self) -> List[TraceEvent]:
        """Return all error events in chronological order."""
        return self.events_by_type(EventType.ERROR_OCCURRED)

    def checkpoint_events(self) -> List[TraceEvent]:
        """Return all checkpoint events in chronological order."""
        created = self.events_by_type(EventType.CHECKPOINT_CREATED)
        restored = self.events_by_type(EventType.CHECKPOINT_RESTORED)
        return sorted(created + restored, key=lambda e: e.timestamp)

    def __iter__(self) -> Iterator[TraceEvent]:
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __bool__(self) -> bool:
        return bool(self.events)

    def __getitem__(self, index: int) -> TraceEvent:
        return self.events[index]


__all__ = [
    "RuntimeTimeline",
]
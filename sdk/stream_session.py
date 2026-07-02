"""Stage-07.4 SDK Streaming session state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4

from .stream_event import StreamEvent
from .stream_models import StreamState


@dataclass
class StreamSession:
    """In-memory streaming session used by SDKStreamingAPI."""

    job_id: str = "sdk-stream-job"
    session_id: str = field(default_factory=lambda: f"sdk-stream-{uuid4().hex[:12]}")
    state: StreamState = field(default_factory=StreamState)
    events: List[StreamEvent] = field(default_factory=list)

    def append(self, event: StreamEvent) -> StreamEvent:
        self.events.append(event)
        self.state.event_count = len(self.events)
        if event.segment_index is not None:
            self.state.current_segment_index = event.segment_index
        if event.type == "started":
            self.state.status = "running"
        elif event.type == "segment":
            self.state.completed_segments += 1
        elif event.type == "completed":
            self.state.status = "completed"
            self.state.current_segment_index = None
        elif event.type == "error":
            self.state.status = "failed"
        return event

    def progress(self) -> StreamState:
        return self.state

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "state": self.state.to_dict(),
            "events": [event.to_dict() for event in self.events],
        }

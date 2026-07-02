"""Stage-07.4 SDK Streaming response objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .stream_event import StreamEvent


@dataclass
class StreamResponse:
    """Final response returned by collected SDK streaming translation."""

    ok: bool
    text: str = ""
    events: List[StreamEvent] = field(default_factory=list)
    job_id: str = "sdk-stream-job"
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def event_count(self) -> int:
        return len(self.events)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "text": self.text,
            "events": [event.to_dict() for event in self.events],
            "job_id": self.job_id,
            "session_id": self.session_id,
            "data": dict(self.data),
            "errors": list(self.errors),
        }

    @classmethod
    def from_events(cls, events: List[StreamEvent], *, job_id: str = "sdk-stream-job", session_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> "StreamResponse":
        errors = [event.error for event in events if event.error]
        completed = [event for event in events if event.type == "completed"]
        text = completed[-1].text if completed else "".join(event.text for event in events if event.type in {"segment", "token"})
        return cls(ok=not errors, text=text, events=list(events), job_id=job_id, session_id=session_id, data=dict(data or {}), errors=[str(item) for item in errors])

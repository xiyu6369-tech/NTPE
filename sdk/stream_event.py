"""Stage-07.4 SDK Streaming event objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StreamEvent:
    """Stable event emitted by the SDK Streaming API."""

    type: str
    sequence: int
    job_id: str = "sdk-stream-job"
    session_id: Optional[str] = None
    segment_index: Optional[int] = None
    text: str = ""
    progress: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "sequence": self.sequence,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "segment_index": self.segment_index,
            "text": self.text,
            "progress": self.progress,
            "data": dict(self.data),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        return cls(
            type=str(data.get("type", "event")),
            sequence=int(data.get("sequence", 0)),
            job_id=str(data.get("job_id", "sdk-stream-job")),
            session_id=data.get("session_id"),
            segment_index=data.get("segment_index"),
            text=str(data.get("text", "")),
            progress=float(data.get("progress", 0.0)),
            data=dict(data.get("data", {}) or {}),
            error=data.get("error"),
        )

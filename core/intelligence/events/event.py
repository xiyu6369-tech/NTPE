"""Foundation-07.5 Intelligence Event primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IntelligenceEvent:
    """Immutable, serializable event used by Intelligence subsystems."""

    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "intelligence"
    scope_key: Optional[str] = None
    segment_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "scope_key": self.scope_key,
            "segment_id": self.segment_id,
            "payload": dict(self.payload or {}),
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligenceEvent":
        return cls(
            event_type=str(data.get("event_type") or data.get("type") or "unknown"),
            payload=dict(data.get("payload") or {}),
            source=str(data.get("source") or "intelligence"),
            scope_key=data.get("scope_key"),
            segment_id=data.get("segment_id"),
            event_id=str(data.get("event_id") or uuid4()),
            timestamp=str(data.get("timestamp") or utc_now_iso()),
            metadata=dict(data.get("metadata") or {}),
        )

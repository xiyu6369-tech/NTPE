"""Runtime Event API request helpers for NTPE 1.0 Beta Stage-11.5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .runtime_event import RuntimeEventSeverity, RuntimeEventType

RUNTIME_EVENT_REQUEST_VERSION = "1.0.0-beta.11.5"
RUNTIME_EVENT_REQUEST_STAGE = "11.5"


@dataclass(frozen=True)
class RuntimeEventPublishRequest:
    """Normalized publish-event payload."""

    name: str
    event_type: RuntimeEventType | str = RuntimeEventType.CUSTOM
    severity: RuntimeEventSeverity | str = RuntimeEventSeverity.INFO
    source: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    message: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = RUNTIME_EVENT_REQUEST_VERSION
    stage = RUNTIME_EVENT_REQUEST_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload or {}))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuntimeEventPublishRequest":
        return cls(
            name=payload.get("name") or payload.get("event") or "runtime.event",
            event_type=payload.get("event_type", RuntimeEventType.CUSTOM),
            severity=payload.get("severity", RuntimeEventSeverity.INFO),
            source=payload.get("source"),
            session_id=payload.get("session_id"),
            job_id=payload.get("job_id"),
            pipeline_id=payload.get("pipeline_id"),
            message=payload.get("message"),
            payload=payload.get("payload") or {},
            metadata=payload.get("metadata") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "message": self.message,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

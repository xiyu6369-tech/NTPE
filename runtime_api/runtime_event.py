"""Runtime Event API models for NTPE 1.0 Beta Stage-11.5.

This module is additive and preserves Stage-11.1 through Stage-11.4 public
contracts. It introduces serializable event descriptors for CLI, SDK, future
REST API, and automation surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

RUNTIME_EVENT_API_VERSION = "1.0.0-beta.11.5"
RUNTIME_EVENT_API_STAGE = "11.5"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimeEventType(str, Enum):
    """Stable Runtime Event API event types."""

    RUNTIME = "runtime"
    SESSION = "session"
    JOB = "job"
    PIPELINE = "pipeline"
    PROVIDER = "provider"
    QUALITY = "quality"
    SYSTEM = "system"
    CUSTOM = "custom"


class RuntimeEventSeverity(str, Enum):
    """Stable Runtime Event API severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RuntimeEvent:
    """Serializable runtime event envelope."""

    name: str
    event_type: RuntimeEventType | str = RuntimeEventType.CUSTOM
    severity: RuntimeEventSeverity | str = RuntimeEventSeverity.INFO
    event_id: str = field(default_factory=lambda: f"runtime-event-{uuid4().hex[:12]}")
    source: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    message: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    version = RUNTIME_EVENT_API_VERSION
    stage = RUNTIME_EVENT_API_STAGE

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            from .runtime_errors import RuntimeApiValidationError

            raise RuntimeApiValidationError("runtime event name is required")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "event_type", RuntimeEventType(self.event_type))
        object.__setattr__(self, "severity", RuntimeEventSeverity(self.severity))
        object.__setattr__(self, "event_id", str(self.event_id))
        object.__setattr__(self, "payload", dict(self.payload or {}))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        for attr in ("source", "session_id", "job_id", "pipeline_id", "message"):
            value = getattr(self, attr)
            if value is not None:
                object.__setattr__(self, attr, str(value))

    def with_metadata(self, **metadata: Any) -> "RuntimeEvent":
        return RuntimeEvent(
            name=self.name,
            event_type=self.event_type,
            severity=self.severity,
            event_id=self.event_id,
            source=self.source,
            session_id=self.session_id,
            job_id=self.job_id,
            pipeline_id=self.pipeline_id,
            message=self.message,
            payload=self.payload,
            metadata={**self.metadata, **dict(metadata or {})},
            created_at=self.created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "event_id": self.event_id,
            "name": self.name,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "source": self.source,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "message": self.message,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

"""RM-6.3.3 Runtime Execution Trace domain models.

Immutable dataclasses for trace events, chunk execution records,
and event type classification. No provider imports. No network calls.
No persistence. No Translation Engine modifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trace_hash(*parts: str) -> str:
    joined = "\x00".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()


def _generate_event_id() -> str:
    raw = uuid4().hex
    return f"evt-{raw[:10]}"


class EventType(str, Enum):
    SESSION_CREATED = "SESSION_CREATED"
    CHUNK_STARTED = "CHUNK_STARTED"
    CHUNK_COMPLETED = "CHUNK_COMPLETED"
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"
    CHECKPOINT_RESTORED = "CHECKPOINT_RESTORED"
    RETRY_STARTED = "RETRY_STARTED"
    RETRY_COMPLETED = "RETRY_COMPLETED"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    SESSION_FAILED = "SESSION_FAILED"


class ChunkStatus(str, Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"


class ErrorSeverity(str, Enum):
    WARNING = "WARNING"
    RECOVERABLE = "RECOVERABLE"
    FATAL = "FATAL"


@dataclass(frozen=True)
class TraceEvent:
    """A single immutable trace event recording one runtime occurrence.

    Stores the event identity, session association, chunk context,
    event type, timestamp, and optional metadata. No provider payload,
    no translated text, no API response is stored.
    """

    event_id: str = field(default_factory=_generate_event_id)
    session_id: str = ""
    chunk_index: int = 0
    event_type: EventType = EventType.SESSION_CREATED
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.3"

    def compute_hash(self) -> str:
        parts: List[str] = [
            self.event_id,
            self.session_id,
            str(self.chunk_index),
            self.event_type.value,
            str(self.metadata),
        ]
        return _trace_hash(*parts)

    def as_tuple(self) -> tuple:
        return (
            self.event_id,
            self.session_id,
            self.chunk_index,
            self.event_type.value,
            self.timestamp,
        )


@dataclass(frozen=True)
class ChunkTrace:
    """Execution record for a single chunk within a translation session.

    Tracks timing, status, retry count, and checkpoint association.
    Immutable — each state transition produces a new instance.
    """

    chunk_index: int = 0
    session_id: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str = ""
    duration_ms: int = 0
    status: ChunkStatus = ChunkStatus.STARTED
    retry_count: int = 0
    checkpoint_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.3"

    def as_tuple(self) -> tuple:
        return (
            self.chunk_index,
            self.session_id,
            self.started_at,
            self.finished_at,
            self.duration_ms,
            self.status.value,
            self.retry_count,
            self.checkpoint_id,
        )


@dataclass(frozen=True)
class RetryRecord:
    """Immutable record of a single retry attempt for a chunk."""

    chunk_index: int = 0
    attempt: int = 1
    error_message: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str = ""
    successful: bool = False

    version: str = "rm-6.3.3"


@dataclass(frozen=True)
class CheckpointRecord:
    """Immutable record of a checkpoint event within the trace."""

    checkpoint_id: str = ""
    chunk_index: int = 0
    session_id: str = ""
    action: str = "CREATED"
    snapshot_id: str = ""
    timestamp: str = field(default_factory=utc_now_iso)

    version: str = "rm-6.3.3"


@dataclass(frozen=True)
class ErrorRecord:
    """Immutable record of an error event within the trace.

    Stores error identity, type classification, severity, and
    message. Does NOT store provider payload, API response, or
    translated content.
    """

    chunk_index: int = 0
    session_id: str = ""
    error_type: str = ""
    severity: ErrorSeverity = ErrorSeverity.RECOVERABLE
    error_message: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.3"


class TraceIntegrityError(ValueError):
    def __init__(self, event_id: str):
        msg = f"Trace integrity check failed for event: {event_id}"
        super().__init__(msg)
        self.event_id = event_id


class TraceEventNotFoundError(ValueError):
    def __init__(self, event_id: str):
        msg = f"Trace event not found: {event_id}"
        super().__init__(msg)
        self.event_id = event_id


__all__ = [
    "TraceEvent",
    "ChunkTrace",
    "RetryRecord",
    "CheckpointRecord",
    "ErrorRecord",
    "EventType",
    "ChunkStatus",
    "ErrorSeverity",
    "TraceIntegrityError",
    "TraceEventNotFoundError",
    "utc_now_iso",
]
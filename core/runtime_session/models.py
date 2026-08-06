"""RM-6.3.1 Runtime Session domain models.

Immutable dataclasses for session state management, runtime state
tracking, and deterministic trace recording. No provider imports.
No network calls. No persistence. No Translation Engine modifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_VALID_TRANSITIONS: Dict[RunStatus, List[RunStatus]] = {
    RunStatus.CREATED: [RunStatus.RUNNING, RunStatus.FAILED],
    RunStatus.RUNNING: [RunStatus.PAUSED, RunStatus.COMPLETED, RunStatus.FAILED],
    RunStatus.PAUSED: [RunStatus.RUNNING, RunStatus.COMPLETED, RunStatus.FAILED],
    RunStatus.COMPLETED: [],
    RunStatus.FAILED: [],
}


def _session_hash(*parts: str) -> str:
    joined = "\x00".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()


def _generate_session_id() -> str:
    raw = uuid4().hex
    return raw[:12]


@dataclass(frozen=True)
class TranslationSession:
    """Immutable container for a translation session.

    Represents one complete translation run. Contains identity,
    progress counters, and runtime metadata. Immutable — concurrent
    access is safe without locks.
    """

    session_id: str = field(default_factory=_generate_session_id)
    created_at: str = field(default_factory=utc_now_iso)
    request_count: int = 0
    chunk_index: int = 0
    snapshot_id: str = ""
    prompt_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.1"


@dataclass(frozen=True)
class RuntimeState:
    """Track current runtime state for a session.

    Coupled to TranslationSession via session_id. State transitions
    are validated against the RunStatus enum. Chunk counters
    monotonically increase per request.
    """

    session_id: str
    current_chunk: int = 0
    total_chunks: int = 0
    status: RunStatus = RunStatus.CREATED
    last_request: str = field(default_factory=utc_now_iso)
    last_response: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.1"

    def can_transition_to(self, target: RunStatus) -> bool:
        allowed = _VALID_TRANSITIONS.get(self.status, [])
        return target in allowed

    def transition(self, target: RunStatus, **kwargs: Any) -> "RuntimeState":
        if not self.can_transition_to(target):
            raise RuntimeStateTransitionError(self.status, target)
        updates: Dict[str, Any] = {"status": target}
        if target == RunStatus.RUNNING:
            updates["last_request"] = utc_now_iso()
        elif target in (RunStatus.COMPLETED, RunStatus.FAILED):
            updates["last_response"] = utc_now_iso()
        updates.update(kwargs)
        return type(self)(
            session_id=self.session_id,
            current_chunk=updates.get("current_chunk", self.current_chunk),
            total_chunks=updates.get("total_chunks", self.total_chunks),
            status=updates.get("status", self.status),
            last_request=updates.get("last_request", self.last_request),
            last_response=updates.get("last_response", self.last_response),
            metadata=updates.get("metadata", self.metadata),
        )


class RuntimeStateTransitionError(ValueError):
    def __init__(self, current: RunStatus, target: RunStatus):
        msg = f"Invalid state transition: {current.value} → {target.value}"
        super().__init__(msg)
        self.current = current
        self.target = target


@dataclass(frozen=True)
class TraceEntry:
    """A single trace entry recording one request event.

    Stores the request identity, snapshot identity, chunk index,
    and timestamp. No provider payload is stored — this is a
    pure identity trace.
    """

    request_hash: str
    snapshot_id: str
    chunk: int
    timestamp: str = field(default_factory=utc_now_iso)

    def as_tuple(self) -> tuple:
        return (
            self.request_hash,
            self.snapshot_id,
            self.chunk,
            self.timestamp,
        )


@dataclass(frozen=True)
class SessionTrace:
    """Ordered sequence of trace entries for a session.

    Each entry corresponds to one request prepared and handed off
    to the Translation Engine. Entries are immutable and maintain
    insertion order.
    """

    session_id: str
    entries: List[TraceEntry] = field(default_factory=list)

    version: str = "rm-6.3.1"

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def append(self, entry: TraceEntry) -> "SessionTrace":
        return SessionTrace(
            session_id=self.session_id,
            entries=self.entries + [entry],
        )


__all__ = [
    "TranslationSession",
    "RuntimeState",
    "RunStatus",
    "SessionTrace",
    "TraceEntry",
    "RuntimeStateTransitionError",
    "_session_hash",
    "_generate_session_id",
    "utc_now_iso",
]
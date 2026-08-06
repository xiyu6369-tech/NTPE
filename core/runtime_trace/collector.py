"""RM-6.3.3 Runtime Trace Collector.

Central aggregation point for runtime trace events. Accepts recording
calls from the runtime layer and builds chronological timelines.

No provider imports. No network calls. No Translation Engine
modifications. No persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .models import (
    EventType,
    ErrorSeverity,
    TraceEvent,
    ChunkTrace,
    ChunkStatus,
    RetryRecord,
    CheckpointRecord,
    ErrorRecord,
)
from .timeline import RuntimeTimeline
from .models import utc_now_iso


@dataclass(frozen=True)
class RuntimeTraceCollector:
    """Aggregate runtime trace events into a session timeline.

    Records are accumulated in the internal ``_events`` list. Each
    recording call returns a new Collector instance (immutable style)
    containing the updated event list. Use ``build_timeline()`` to
    produce a final ``RuntimeTimeline``.
    """

    session_id: str = ""
    _events: List[TraceEvent] = field(default_factory=list, repr=False)
    _chunks: List[ChunkTrace] = field(default_factory=list, repr=False)
    _retries: List[RetryRecord] = field(default_factory=list, repr=False)
    _checkpoints: List[CheckpointRecord] = field(default_factory=list, repr=False)
    _errors: List[ErrorRecord] = field(default_factory=list, repr=False)

    version: str = "rm-6.3.3"

    def record_event(
        self,
        event_type: EventType,
        chunk_index: int = 0,
        metadata: Dict[str, Any] | None = None,
    ) -> RuntimeTraceCollector:
        event = TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=event_type,
            metadata=metadata or {},
        )
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks,
            _retries=self._retries,
            _checkpoints=self._checkpoints,
            _errors=self._errors,
        )

    def record_chunk_start(self, chunk_index: int) -> RuntimeTraceCollector:
        chunk = ChunkTrace(
            chunk_index=chunk_index,
            session_id=self.session_id,
            started_at=utc_now_iso(),
            status=ChunkStatus.STARTED,
        )
        event = TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=EventType.CHUNK_STARTED,
            metadata={"chunk_index": chunk_index},
        )
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks + [chunk],
            _retries=self._retries,
            _checkpoints=self._checkpoints,
            _errors=self._errors,
        )

    def record_chunk_finish(
        self,
        chunk_index: int,
        duration_ms: int = 0,
        checkpoint_id: str = "",
    ) -> RuntimeTraceCollector:
        finished_at = utc_now_iso()
        chunk = ChunkTrace(
            chunk_index=chunk_index,
            session_id=self.session_id,
            started_at=finished_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            status=ChunkStatus.COMPLETED,
            retry_count=0,
            checkpoint_id=checkpoint_id,
        )
        event = self._chunk_finish_event(chunk_index, duration_ms)
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks + [chunk],
            _retries=self._retries,
            _checkpoints=self._checkpoints,
            _errors=self._errors,
        )

    def record_retry(
        self,
        chunk_index: int,
        attempt: int = 1,
        error_message: str = "",
        successful: bool = False,
    ) -> RuntimeTraceCollector:
        finished_at = utc_now_iso()
        retry = RetryRecord(
            chunk_index=chunk_index,
            attempt=attempt,
            error_message=error_message,
            started_at=finished_at,
            finished_at=finished_at,
            successful=successful,
        )
        event_type = EventType.RETRY_COMPLETED if successful else EventType.RETRY_STARTED
        event = TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=event_type,
            metadata={
                "attempt": attempt,
                "successful": successful,
            },
        )
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks,
            _retries=self._retries + [retry],
            _checkpoints=self._checkpoints,
            _errors=self._errors,
        )

    def record_checkpoint(
        self,
        checkpoint_id: str = "",
        chunk_index: int = 0,
        action: str = "CREATED",
        snapshot_id: str = "",
    ) -> RuntimeTraceCollector:
        checkpoint = CheckpointRecord(
            checkpoint_id=checkpoint_id,
            chunk_index=chunk_index,
            session_id=self.session_id,
            action=action,
            snapshot_id=snapshot_id,
            timestamp=utc_now_iso(),
        )
        event_type = (
            EventType.CHECKPOINT_CREATED if action == "CREATED" else EventType.CHECKPOINT_RESTORED
        )
        event = TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=event_type,
            metadata={
                "checkpoint_id": checkpoint_id,
                "action": action,
                "snapshot_id": snapshot_id,
            },
        )
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks,
            _retries=self._retries,
            _checkpoints=self._checkpoints + [checkpoint],
            _errors=self._errors,
        )

    def record_error(
        self,
        chunk_index: int = 0,
        error_type: str = "",
        severity: ErrorSeverity = ErrorSeverity.RECOVERABLE,
        error_message: str = "",
        metadata: Dict[str, Any] | None = None,
    ) -> RuntimeTraceCollector:
        error = ErrorRecord(
            chunk_index=chunk_index,
            session_id=self.session_id,
            error_type=error_type,
            severity=severity,
            error_message=error_message,
            timestamp=utc_now_iso(),
            metadata=metadata or {},
        )
        event = TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=EventType.ERROR_OCCURRED,
            metadata={
                "error_type": error_type,
                "severity": severity.value,
                "error_message": error_message,
            },
        )
        return RuntimeTraceCollector(
            session_id=self.session_id,
            _events=self._events + [event],
            _chunks=self._chunks,
            _retries=self._retries,
            _checkpoints=self._checkpoints,
            _errors=self._errors + [error],
        )

    def build_timeline(self) -> RuntimeTimeline:
        timeline = RuntimeTimeline(session_id=self.session_id, events=[])
        for event in self._events:
            timeline = timeline.append_event(event)
        return timeline

    @property
    def chunks(self) -> List[ChunkTrace]:
        return list(self._chunks)

    @property
    def retries(self) -> List[RetryRecord]:
        return list(self._retries)

    @property
    def checkpoints(self) -> List[CheckpointRecord]:
        return list(self._checkpoints)

    @property
    def errors(self) -> List[ErrorRecord]:
        return list(self._errors)

    def _chunk_finish_event(self, chunk_index: int, duration_ms: int) -> TraceEvent:
        return TraceEvent(
            session_id=self.session_id,
            chunk_index=chunk_index,
            event_type=EventType.CHUNK_COMPLETED,
            metadata={
                "chunk_index": chunk_index,
                "duration_ms": duration_ms,
            },
        )


__all__ = [
    "RuntimeTraceCollector",
]
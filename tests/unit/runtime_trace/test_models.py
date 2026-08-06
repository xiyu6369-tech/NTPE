"""Tests for Runtime Trace models (RM-6.3.3)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_trace.models import (
    TraceEvent,
    ChunkTrace,
    RetryRecord,
    CheckpointRecord,
    ErrorRecord,
    EventType,
    ChunkStatus,
    ErrorSeverity,
    utc_now_iso,
    _generate_event_id,
    _trace_hash,
)


class TestTraceEvent:
    def test_create_event(self):
        event = TraceEvent(
            session_id="s1",
            chunk_index=2,
            event_type=EventType.CHUNK_STARTED,
        )
        assert event.event_id.startswith("evt-")
        assert event.session_id == "s1"
        assert event.chunk_index == 2
        assert event.event_type == EventType.CHUNK_STARTED
        assert event.timestamp

    def test_unique_event_id(self):
        e1 = TraceEvent()
        e2 = TraceEvent()
        assert e1.event_id != e2.event_id
        assert len(e1.event_id) == 14

    def test_immutable(self):
        event = TraceEvent()
        with pytest.raises(FrozenInstanceError):
            event.session_id = "changed"

    def test_defaults(self):
        event = TraceEvent()
        assert event.session_id == ""
        assert event.chunk_index == 0
        assert event.event_type == EventType.SESSION_CREATED
        assert event.metadata == {}
        assert event.version == "rm-6.3.3"

    def test_with_values(self):
        event = TraceEvent(
            session_id="abc",
            chunk_index=5,
            event_type=EventType.ERROR_OCCURRED,
            metadata={"reason": "timeout"},
        )
        assert event.session_id == "abc"
        assert event.chunk_index == 5
        assert event.event_type == EventType.ERROR_OCCURRED
        assert event.metadata == {"reason": "timeout"}

    def test_equality_same_id(self):
        timestamp = "2026-01-01T00:00:00"
        e1 = TraceEvent(event_id="evt-001", session_id="s1", chunk_index=1,
                        event_type=EventType.CHUNK_COMPLETED, timestamp=timestamp)
        e2 = TraceEvent(event_id="evt-001", session_id="s1", chunk_index=1,
                        event_type=EventType.CHUNK_COMPLETED, timestamp=timestamp)
        assert e1.event_id == e2.event_id
        assert e1.session_id == e2.session_id
        assert e1.chunk_index == e2.chunk_index
        assert e1.event_type == e2.event_type

    def test_inequality(self):
        e1 = TraceEvent(event_id="evt-001")
        e2 = TraceEvent(event_id="evt-002")
        assert e1 != e2

    def test_hash_deterministic(self):
        e1 = TraceEvent(event_id="a", session_id="s", chunk_index=0,
                        event_type=EventType.SESSION_CREATED, metadata={})
        e2 = TraceEvent(event_id="a", session_id="s", chunk_index=0,
                        event_type=EventType.SESSION_CREATED, metadata={})
        assert e1.compute_hash() == e2.compute_hash()

    def test_hash_different_for_different_metadata(self):
        e1 = TraceEvent(event_id="a", metadata={"k": "v1"})
        e2 = TraceEvent(event_id="a", metadata={"k": "v2"})
        assert e1.compute_hash() != e2.compute_hash()

    def test_as_tuple(self):
        event = TraceEvent(
            session_id="s1",
            chunk_index=3,
            event_type=EventType.CHUNK_STARTED,
        )
        tup = event.as_tuple()
        assert tup[0] == event.event_id
        assert tup[1] == "s1"
        assert tup[2] == 3
        assert tup[3] == "CHUNK_STARTED"
        assert tup[4] == event.timestamp


class TestEventType:
    def test_enum_values(self):
        assert EventType.SESSION_CREATED.value == "SESSION_CREATED"
        assert EventType.CHUNK_STARTED.value == "CHUNK_STARTED"
        assert EventType.CHUNK_COMPLETED.value == "CHUNK_COMPLETED"
        assert EventType.CHECKPOINT_CREATED.value == "CHECKPOINT_CREATED"
        assert EventType.CHECKPOINT_RESTORED.value == "CHECKPOINT_RESTORED"
        assert EventType.RETRY_STARTED.value == "RETRY_STARTED"
        assert EventType.RETRY_COMPLETED.value == "RETRY_COMPLETED"
        assert EventType.ERROR_OCCURRED.value == "ERROR_OCCURRED"
        assert EventType.SESSION_COMPLETED.value == "SESSION_COMPLETED"
        assert EventType.SESSION_FAILED.value == "SESSION_FAILED"

    def test_str_enum(self):
        assert EventType.SESSION_CREATED == "SESSION_CREATED"

    def test_membership_count(self):
        assert len(list(EventType)) == 10


class TestChunkTrace:
    def test_create_chunk(self):
        chunk = ChunkTrace(
            chunk_index=0,
            session_id="s1",
        )
        assert chunk.chunk_index == 0
        assert chunk.session_id == "s1"
        assert chunk.started_at
        assert chunk.finished_at == ""
        assert chunk.duration_ms == 0
        assert chunk.status == ChunkStatus.STARTED
        assert chunk.retry_count == 0
        assert chunk.checkpoint_id == ""

    def test_immutable(self):
        chunk = ChunkTrace()
        with pytest.raises(FrozenInstanceError):
            chunk.chunk_index = 99

    def test_defaults(self):
        chunk = ChunkTrace()
        assert chunk.chunk_index == 0
        assert chunk.session_id == ""
        assert chunk.status == ChunkStatus.STARTED

    def test_with_values(self):
        chunk = ChunkTrace(
            chunk_index=5,
            session_id="ses",
            duration_ms=150,
            status=ChunkStatus.COMPLETED,
            retry_count=2,
            checkpoint_id="ckpt-abc",
        )
        assert chunk.chunk_index == 5
        assert chunk.duration_ms == 150
        assert chunk.status == ChunkStatus.COMPLETED
        assert chunk.retry_count == 2
        assert chunk.checkpoint_id == "ckpt-abc"

    def test_as_tuple(self):
        chunk = ChunkTrace(
            chunk_index=1,
            session_id="s1",
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            duration_ms=1000,
            status=ChunkStatus.COMPLETED,
            retry_count=0,
            checkpoint_id="ckpt-001",
        )
        tup = chunk.as_tuple()
        assert tup[0] == 1
        assert tup[1] == "s1"
        assert tup[2] == "2026-01-01T00:00:00Z"
        assert tup[3] == "2026-01-01T00:00:01Z"
        assert tup[4] == 1000
        assert tup[5] == "COMPLETED"
        assert tup[6] == 0
        assert tup[7] == "ckpt-001"

    def test_equality(self):
        c1 = ChunkTrace(chunk_index=3, session_id="s", started_at="t",
                        status=ChunkStatus.COMPLETED)
        c2 = ChunkTrace(chunk_index=3, session_id="s", started_at="t",
                        status=ChunkStatus.COMPLETED)
        assert c1 == c2

    def test_inequality(self):
        c1 = ChunkTrace(chunk_index=1)
        c2 = ChunkTrace(chunk_index=2)
        assert c1 != c2


class TestRetryRecord:
    def test_create_retry(self):
        retry = RetryRecord(chunk_index=0, attempt=1)
        assert retry.chunk_index == 0
        assert retry.attempt == 1
        assert retry.error_message == ""
        assert retry.started_at
        assert retry.finished_at == ""
        assert retry.successful is False

    def test_immutable(self):
        retry = RetryRecord()
        with pytest.raises(FrozenInstanceError):
            retry.attempt = 99

    def test_successful(self):
        retry = RetryRecord(attempt=1, successful=True)
        assert retry.successful is True


class TestCheckpointRecord:
    def test_create_checkpoint(self):
        cp = CheckpointRecord(
            checkpoint_id="ckpt-abc",
            chunk_index=3,
            session_id="s1",
            action="CREATED",
            snapshot_id="snap-001",
        )
        assert cp.checkpoint_id == "ckpt-abc"
        assert cp.session_id == "s1"
        assert cp.action == "CREATED"
        assert cp.snapshot_id == "snap-001"
        assert cp.timestamp

    def test_immutable(self):
        cp = CheckpointRecord()
        with pytest.raises(FrozenInstanceError):
            cp.checkpoint_id = "changed"

    def test_defaults(self):
        cp = CheckpointRecord()
        assert cp.checkpoint_id == ""
        assert cp.chunk_index == 0
        assert cp.action == "CREATED"
        assert cp.snapshot_id == ""


class TestErrorRecord:
    def test_create_error(self):
        error = ErrorRecord(
            chunk_index=2,
            session_id="s1",
            error_type="ProviderTimeout",
            severity=ErrorSeverity.FATAL,
            error_message="Connection lost",
        )
        assert error.chunk_index == 2
        assert error.session_id == "s1"
        assert error.error_type == "ProviderTimeout"
        assert error.severity == ErrorSeverity.FATAL
        assert error.error_message == "Connection lost"
        assert error.timestamp

    def test_immutable(self):
        error = ErrorRecord()
        with pytest.raises(FrozenInstanceError):
            error.error_message = "changed"

    def test_defaults(self):
        error = ErrorRecord()
        assert error.chunk_index == 0
        assert error.session_id == ""
        assert error.error_type == ""
        assert error.severity == ErrorSeverity.RECOVERABLE
        assert error.error_message == ""
        assert error.metadata == {}


class TestErrorSeverity:
    def test_enum_values(self):
        assert ErrorSeverity.WARNING.value == "WARNING"
        assert ErrorSeverity.RECOVERABLE.value == "RECOVERABLE"
        assert ErrorSeverity.FATAL.value == "FATAL"


class TestDeterministicHash:
    def test_same_inputs_same_hash(self):
        h1 = _trace_hash("a", "b")
        h2 = _trace_hash("a", "b")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = _trace_hash("a", "b")
        h2 = _trace_hash("a", "c")
        assert h1 != h2

    def test_length(self):
        h = _trace_hash("hello")
        assert len(h) == 64


class TestUtcNowIso:
    def test_returns_string(self):
        ts = utc_now_iso()
        assert isinstance(ts, str)

    def test_contains_t(self):
        ts = utc_now_iso()
        assert "T" in ts

    def test_two_calls_different(self):
        t1 = utc_now_iso()
        t2 = utc_now_iso()
        assert t1 != t2


class TestGenerateEventId:
    def test_returns_string(self):
        eid = _generate_event_id()
        assert isinstance(eid, str)
        assert eid.startswith("evt-")
        assert len(eid) == 14

    def test_unique(self):
        ids = {_generate_event_id() for _ in range(100)}
        assert len(ids) == 100
"""Tests for RuntimeTraceCollector (RM-6.3.3)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_trace.collector import RuntimeTraceCollector
from core.runtime_trace.models import (
    ChunkTrace,
    EventType,
    ErrorSeverity,
    ChunkStatus,
)
from core.runtime_trace.timeline import RuntimeTimeline


class TestRuntimeTraceCollector:
    def test_initial_state(self):
        collector = RuntimeTraceCollector(session_id="s1")
        assert collector.session_id == "s1"
        assert len(collector.chunks) == 0
        assert len(collector.retries) == 0
        assert len(collector.checkpoints) == 0
        assert len(collector.errors) == 0

    def test_record_session_created(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_event(EventType.SESSION_CREATED)
        assert len(collector.chunks) == 0
        timeline = c2.build_timeline()
        assert timeline.event_count == 1
        assert timeline.events[0].event_type == EventType.SESSION_CREATED
        assert timeline.events[0].session_id == "s1"

    def test_record_chunk_start(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_chunk_start(chunk_index=0)
        assert len(c2.chunks) == 1
        assert c2.chunks[0].chunk_index == 0
        assert c2.chunks[0].status == ChunkStatus.STARTED
        timeline = c2.build_timeline()
        assert timeline.event_count == 1
        assert timeline.events[0].event_type == EventType.CHUNK_STARTED

    def test_record_chunk_finish(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_chunk_finish(
            chunk_index=0,
            duration_ms=100,
            checkpoint_id="ckpt-1",
        )
        assert len(c2.chunks) == 1
        assert c2.chunks[0].status == ChunkStatus.COMPLETED
        assert c2.chunks[0].duration_ms == 100
        assert c2.chunks[0].checkpoint_id == "ckpt-1"
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.CHUNK_COMPLETED

    def test_record_retry_successful(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_retry(
            chunk_index=1,
            attempt=2,
            error_message="timeout",
            successful=True,
        )
        assert len(c2.retries) == 1
        assert c2.retries[0].attempt == 2
        assert c2.retries[0].successful is True
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.RETRY_COMPLETED

    def test_record_retry_failed(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_retry(
            chunk_index=1,
            attempt=1,
            error_message="timeout",
            successful=False,
        )
        assert len(c2.retries) == 1
        assert c2.retries[0].successful is False
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.RETRY_STARTED

    def test_record_checkpoint_created(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_checkpoint(
            checkpoint_id="ckpt-a",
            chunk_index=5,
            action="CREATED",
            snapshot_id="snap-1",
        )
        assert len(c2.checkpoints) == 1
        assert c2.checkpoints[0].checkpoint_id == "ckpt-a"
        assert c2.checkpoints[0].action == "CREATED"
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.CHECKPOINT_CREATED

    def test_record_checkpoint_restored(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_checkpoint(
            checkpoint_id="ckpt-b",
            chunk_index=3,
            action="RESTORED",
            snapshot_id="snap-2",
        )
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.CHECKPOINT_RESTORED

    def test_record_error(self):
        collector = RuntimeTraceCollector(session_id="s1")
        c2 = collector.record_error(
            chunk_index=2,
            error_type="ProviderError",
            severity=ErrorSeverity.FATAL,
            error_message="Connection lost",
        )
        assert len(c2.errors) == 1
        assert c2.errors[0].error_type == "ProviderError"
        assert c2.errors[0].severity == ErrorSeverity.FATAL
        assert c2.errors[0].error_message == "Connection lost"
        timeline = c2.build_timeline()
        assert timeline.events[0].event_type == EventType.ERROR_OCCURRED

    def test_ordering_multiple_events(self):
        collector = RuntimeTraceCollector(session_id="s1")
        collector = collector.record_event(EventType.SESSION_CREATED)
        collector = collector.record_chunk_start(chunk_index=0)
        collector = collector.record_chunk_finish(chunk_index=0, duration_ms=50)
        collector = collector.record_chunk_start(chunk_index=1)
        collector = collector.record_error(chunk_index=1, error_type="Err",
                                           error_message="fail")
        timeline = collector.build_timeline()

        assert timeline.event_count == 5
        assert timeline.events[0].event_type == EventType.SESSION_CREATED
        assert timeline.events[1].event_type == EventType.CHUNK_STARTED
        assert timeline.events[2].event_type == EventType.CHUNK_COMPLETED
        assert timeline.events[3].event_type == EventType.CHUNK_STARTED
        assert timeline.events[4].event_type == EventType.ERROR_OCCURRED

    def test_full_session_lifecycle(self):
        collector = RuntimeTraceCollector(session_id="s-lifecycle")
        collector = collector.record_event(EventType.SESSION_CREATED)
        collector = collector.record_chunk_start(chunk_index=0)
        collector = collector.record_chunk_finish(chunk_index=0, duration_ms=200)
        collector = collector.record_checkpoint(
            checkpoint_id="ckpt-life", chunk_index=0,
            action="CREATED", snapshot_id="s-1",
        )
        collector = collector.record_event(EventType.SESSION_COMPLETED)
        timeline = collector.build_timeline()

        assert timeline.event_count == 5
        types = [e.event_type for e in timeline.events]
        assert types == [
            EventType.SESSION_CREATED,
            EventType.CHUNK_STARTED,
            EventType.CHUNK_COMPLETED,
            EventType.CHECKPOINT_CREATED,
            EventType.SESSION_COMPLETED,
        ]

    def test_build_timeline_returns_runtime_timeline(self):
        collector = RuntimeTraceCollector(session_id="s1")
        collector = collector.record_event(EventType.SESSION_CREATED)
        timeline = collector.build_timeline()
        assert isinstance(timeline, RuntimeTimeline)
        assert timeline.session_id == "s1"

    def test_chunks_property_no_modify(self):
        collector = RuntimeTraceCollector(session_id="s1")
        collector = collector.record_chunk_start(chunk_index=0)
        collector = collector.record_chunk_finish(chunk_index=0, duration_ms=10)
        c = collector.chunks
        c.append(ChunkTrace(chunk_index=99))
        assert len(collector.chunks) == 2


class TestCollectorImmutability:
    def test_record_event_returns_new_instance(self):
        c1 = RuntimeTraceCollector(session_id="s1")
        c2 = c1.record_event(EventType.SESSION_CREATED)
        assert c1 is not c2
        timeline1 = c1.build_timeline()
        timeline2 = c2.build_timeline()
        assert timeline1.event_count == 0
        assert timeline2.event_count == 1
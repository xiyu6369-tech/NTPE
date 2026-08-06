"""Tests for RuntimeTimeline (RM-6.3.3)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_trace.models import EventType, TraceEvent
from core.runtime_trace.timeline import RuntimeTimeline


def _make_event(session_id="s1", chunk_index=0,
                event_type=EventType.SESSION_CREATED, metadata=None):
    return TraceEvent(
        session_id=session_id,
        chunk_index=chunk_index,
        event_type=event_type,
        metadata=metadata or {},
    )


class TestRuntimeTimeline:
    def test_empty_timeline(self):
        tl = RuntimeTimeline(session_id="s1")
        assert tl.session_id == "s1"
        assert tl.event_count == 0
        assert len(tl) == 0
        assert not tl
        assert tl.latest_event() is None
        assert tl.first_event() is None

    def test_append_event(self):
        tl = RuntimeTimeline(session_id="s1")
        e = _make_event(event_type=EventType.CHUNK_STARTED)
        tl2 = tl.append_event(e)
        assert tl.event_count == 0
        assert tl2.event_count == 1
        assert tl2.events[0].event_type == EventType.CHUNK_STARTED

    def test_latest_event(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.SESSION_CREATED, chunk_index=0)
        e2 = _make_event(event_type=EventType.CHUNK_STARTED, chunk_index=0)
        tl = tl.append_event(e1).append_event(e2)
        assert tl.latest_event().event_type == EventType.CHUNK_STARTED

    def test_first_event(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.SESSION_CREATED)
        e2 = _make_event(event_type=EventType.CHUNK_STARTED)
        tl = tl.append_event(e1).append_event(e2)
        assert tl.first_event().event_type == EventType.SESSION_CREATED

    def test_events_for_chunk(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(chunk_index=0, event_type=EventType.CHUNK_STARTED)
        e2 = _make_event(chunk_index=1, event_type=EventType.CHUNK_STARTED)
        e3 = _make_event(chunk_index=0, event_type=EventType.CHUNK_COMPLETED)
        tl = tl.append_event(e1).append_event(e2).append_event(e3)
        chunk0 = tl.events_for_chunk(0)
        assert len(chunk0) == 2
        for e in chunk0:
            assert e.chunk_index == 0

    def test_events_for_session(self):
        tl = RuntimeTimeline(session_id="")
        e1 = _make_event(session_id="s1", event_type=EventType.SESSION_CREATED)
        e2 = _make_event(session_id="s2", event_type=EventType.SESSION_CREATED)
        e3 = _make_event(session_id="s1", event_type=EventType.CHUNK_STARTED)
        tl = tl.append_event(e1).append_event(e2).append_event(e3)
        s1_events = tl.events_for_session("s1")
        assert len(s1_events) == 2
        s2_events = tl.events_for_session("s2")
        assert len(s2_events) == 1

    def test_events_by_type(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.SESSION_CREATED)
        e2 = _make_event(event_type=EventType.ERROR_OCCURRED, metadata={"msg": "e1"})
        e3 = _make_event(event_type=EventType.ERROR_OCCURRED, metadata={"msg": "e2"})
        tl = tl.append_event(e1).append_event(e2).append_event(e3)
        errors = tl.events_by_type(EventType.ERROR_OCCURRED)
        assert len(errors) == 2
        assert errors[0].metadata["msg"] == "e1"
        assert errors[1].metadata["msg"] == "e2"

    def test_retry_events(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.RETRY_STARTED, chunk_index=0)
        e2 = _make_event(event_type=EventType.CHUNK_STARTED, chunk_index=0)
        e3 = _make_event(event_type=EventType.RETRY_COMPLETED, chunk_index=0)
        tl = tl.append_event(e1).append_event(e2).append_event(e3)
        retries = tl.retry_events()
        assert len(retries) == 2
        rt = {e.event_type for e in retries}
        assert rt == {EventType.RETRY_STARTED, EventType.RETRY_COMPLETED}

    def test_error_events(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.CHUNK_STARTED)
        e2 = _make_event(event_type=EventType.ERROR_OCCURRED)
        tl = tl.append_event(e1).append_event(e2)
        errors = tl.error_events()
        assert len(errors) == 1
        assert errors[0].event_type == EventType.ERROR_OCCURRED

    def test_checkpoint_events(self):
        tl = RuntimeTimeline(session_id="s1")
        e1 = _make_event(event_type=EventType.CHECKPOINT_CREATED, chunk_index=0)
        e2 = _make_event(event_type=EventType.CHECKPOINT_RESTORED, chunk_index=0)
        tl = tl.append_event(e1).append_event(e2)
        cps = tl.checkpoint_events()
        assert len(cps) == 2

    def test_deterministic_iteration(self):
        tl = RuntimeTimeline(session_id="s1")
        events = [
            _make_event(chunk_index=i, event_type=EventType.CHUNK_STARTED)
            for i in range(5)
        ]
        for e in events:
            tl = tl.append_event(e)

        iter1 = [e.chunk_index for e in tl]
        iter2 = [e.chunk_index for e in tl]
        assert iter1 == iter2
        assert iter1 == [0, 1, 2, 3, 4]

    def test_len(self):
        tl = RuntimeTimeline(session_id="s1")
        assert len(tl) == 0
        for i in range(3):
            tl = tl.append_event(_make_event(chunk_index=i))
        assert len(tl) == 3

    def test_bool_empty(self):
        tl = RuntimeTimeline(session_id="s1")
        assert not tl

    def test_bool_non_empty(self):
        tl = RuntimeTimeline(session_id="s1")
        tl = tl.append_event(_make_event())
        assert tl

    def test_getitem(self):
        tl = RuntimeTimeline(session_id="s1")
        e0 = _make_event(chunk_index=0)
        e1 = _make_event(chunk_index=1)
        tl = tl.append_event(e0).append_event(e1)
        assert tl[0] is e0
        assert tl[1] is e1

    def test_immutable(self):
        tl = RuntimeTimeline(session_id="s1")
        with pytest.raises(FrozenInstanceError):
            tl.events = []

    def test_session_replay_ordering(self):
        """Simulate a full session and verify chronological ordering."""
        tl = RuntimeTimeline(session_id="replay")
        tl = tl.append_event(_make_event(event_type=EventType.SESSION_CREATED))
        tl = tl.append_event(_make_event(event_type=EventType.CHUNK_STARTED, chunk_index=0))
        tl = tl.append_event(_make_event(event_type=EventType.CHUNK_COMPLETED, chunk_index=0))
        tl = tl.append_event(_make_event(event_type=EventType.CHECKPOINT_CREATED, chunk_index=0))
        tl = tl.append_event(_make_event(event_type=EventType.CHUNK_STARTED, chunk_index=1))
        tl = tl.append_event(_make_event(event_type=EventType.ERROR_OCCURRED, chunk_index=1))
        tl = tl.append_event(_make_event(event_type=EventType.RETRY_STARTED, chunk_index=1))
        tl = tl.append_event(_make_event(event_type=EventType.RETRY_COMPLETED, chunk_index=1))
        tl = tl.append_event(_make_event(event_type=EventType.CHUNK_COMPLETED, chunk_index=1))
        tl = tl.append_event(_make_event(event_type=EventType.SESSION_COMPLETED))

        assert len(tl) == 10
        ordered_types = [e.event_type for e in tl]
        assert ordered_types == [
            EventType.SESSION_CREATED,
            EventType.CHUNK_STARTED,
            EventType.CHUNK_COMPLETED,
            EventType.CHECKPOINT_CREATED,
            EventType.CHUNK_STARTED,
            EventType.ERROR_OCCURRED,
            EventType.RETRY_STARTED,
            EventType.RETRY_COMPLETED,
            EventType.CHUNK_COMPLETED,
            EventType.SESSION_COMPLETED,
        ]
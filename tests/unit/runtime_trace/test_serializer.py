"""Tests for Runtime Trace Serializer (RM-6.3.3)."""

import json

from core.runtime_trace.models import EventType, TraceEvent
from core.runtime_trace.timeline import RuntimeTimeline
from core.runtime_trace.serializer import (
    to_dict,
    to_json,
    from_dict,
    from_json,
)


def _build_timeline(session_id="s1", num_events=3):
    tl = RuntimeTimeline(session_id=session_id)
    for i in range(num_events):
        event = TraceEvent(
            session_id=session_id,
            chunk_index=i,
            event_type=EventType.CHUNK_STARTED,
            metadata={"seq": i},
        )
        tl = tl.append_event(event)
    return tl


class TestToDict:
    def test_produces_dict(self):
        tl = _build_timeline(session_id="s-dict")
        d = to_dict(tl)
        assert isinstance(d, dict)

    def test_contains_session_id(self):
        tl = _build_timeline(session_id="abc")
        d = to_dict(tl)
        assert d["session_id"] == "abc"

    def test_contains_event_count(self):
        tl = _build_timeline(num_events=5)
        d = to_dict(tl)
        assert d["event_count"] == 5

    def test_contains_version(self):
        tl = _build_timeline()
        d = to_dict(tl)
        assert d["version"] == "rm-6.3.3"

    def test_contains_events_list(self):
        tl = _build_timeline(num_events=3)
        d = to_dict(tl)
        assert len(d["events"]) == 3

    def test_event_has_required_fields(self):
        tl = _build_timeline(num_events=1)
        d = to_dict(tl)
        e = d["events"][0]
        for field in ("event_id", "session_id", "chunk_index",
                      "event_type", "timestamp", "metadata"):
            assert field in e

    def test_event_type_is_string(self):
        tl = _build_timeline(num_events=1)
        d = to_dict(tl)
        assert d["events"][0]["event_type"] == "CHUNK_STARTED"

    def test_metadata_preserved(self):
        tl = _build_timeline(num_events=1)
        d = to_dict(tl)
        assert d["events"][0]["metadata"]["seq"] == 0

    def test_empty_timeline(self):
        tl = RuntimeTimeline(session_id="empty")
        d = to_dict(tl)
        assert d["session_id"] == "empty"
        assert d["event_count"] == 0
        assert d["events"] == []


class TestToJson:
    def test_produces_json_string(self):
        tl = _build_timeline()
        j = to_json(tl)
        assert isinstance(j, str)

    def test_valid_json(self):
        tl = _build_timeline()
        j = to_json(tl)
        parsed = json.loads(j)
        assert isinstance(parsed, dict)
        assert parsed["session_id"] == "s1"

    def test_deterministic_for_same_input(self):
        tl = _build_timeline(num_events=2)
        j1 = to_json(tl)
        j2 = to_json(tl)
        assert j1 == j2

    def test_preserves_event_count(self):
        tl = _build_timeline(num_events=7)
        j = to_json(tl)
        parsed = json.loads(j)
        assert parsed["event_count"] == 7


class TestFromDict:
    def test_roundtrip(self):
        tl = _build_timeline(session_id="roundtrip")
        d = to_dict(tl)
        tl2 = from_dict(d)
        assert tl2.session_id == tl.session_id
        assert tl2.event_count == tl.event_count

    def test_event_fields_roundtrip(self):
        tl = _build_timeline(num_events=2)
        d = to_dict(tl)
        tl2 = from_dict(d)
        for e1, e2 in zip(tl.events, tl2.events):
            assert e1.event_id == e2.event_id
            assert e1.session_id == e2.session_id
            assert e1.chunk_index == e2.chunk_index
            assert e1.event_type == e2.event_type
            assert e1.metadata == e2.metadata

    def test_unknown_fields_ignored(self):
        d = {
            "session_id": "s-ignore",
            "version": "rm-6.3.3",
            "event_count": 1,
            "events": [{
                "event_id": "evt-test1",
                "session_id": "s-ignore",
                "chunk_index": 0,
                "event_type": "SESSION_CREATED",
                "timestamp": "2026-01-01T00:00:00",
                "metadata": {},
                "extra_field": "should_be_ignored",
            }],
            "unknown_top_level": "ignored",
        }
        tl = from_dict(d)
        assert tl.session_id == "s-ignore"
        assert tl.event_count == 1

    def test_empty_events_list(self):
        d = {"session_id": "empty", "version": "rm-6.3.3",
             "event_count": 0, "events": []}
        tl = from_dict(d)
        assert tl.event_count == 0

    def test_missing_events_key(self):
        d = {"session_id": "missing", "version": "rm-6.3.3",
             "event_count": 0}
        tl = from_dict(d)
        assert tl.event_count == 0


class TestFromJson:
    def test_roundtrip(self):
        tl = _build_timeline(session_id="json-rt")
        j = to_json(tl)
        tl2 = from_json(j)
        assert tl2.session_id == tl.session_id
        assert tl2.event_count == tl.event_count

        for e1, e2 in zip(tl.events, tl2.events):
            assert e1.event_id == e2.event_id
            assert e1.event_type == e2.event_type

    def test_deterministic_output(self):
        tl = _build_timeline(num_events=3)
        j = to_json(tl)
        tl2 = from_json(j)
        j2 = to_json(tl2)
        parsed = json.loads(j2)
        assert parsed["event_count"] == 3

    def test_metadata_integrity(self):
        tl = RuntimeTimeline(session_id="meta")
        event = TraceEvent(
            session_id="meta",
            chunk_index=5,
            event_type=EventType.ERROR_OCCURRED,
            metadata={"error_code": "E001", "severity": "FATAL"},
        )
        tl = tl.append_event(event)
        j = to_json(tl)
        tl2 = from_json(j)
        assert tl2.events[0].metadata["error_code"] == "E001"
        assert tl2.events[0].metadata["severity"] == "FATAL"
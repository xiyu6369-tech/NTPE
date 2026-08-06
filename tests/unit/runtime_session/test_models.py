"""Tests for Runtime Session models (RM-6.3.1)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_session.models import (
    TranslationSession,
    RuntimeState,
    RunStatus,
    SessionTrace,
    TraceEntry,
    RuntimeStateTransitionError,
    _session_hash,
    _generate_session_id,
    utc_now_iso,
)


class TestTranslationSession:
    def test_create_session(self):
        session = TranslationSession(
            snapshot_id="snap-001",
            prompt_hash="abc123",
            metadata={"novel": "Test"},
        )
        assert session.created_at

    def test_unique_session_id(self):
        s1 = TranslationSession()
        s2 = TranslationSession()
        assert s1.session_id != s2.session_id
        assert len(s1.session_id) == 12

    def test_immutable(self):
        session = TranslationSession()
        with pytest.raises(FrozenInstanceError):
            session.session_id = "changed"

    def test_defaults(self):
        session = TranslationSession()
        assert session.request_count == 0
        assert session.chunk_index == 0
        assert session.snapshot_id == ""
        assert session.prompt_hash == ""
        assert session.metadata == {}
        assert session.version == "rm-6.3.1"

    def test_with_values(self):
        session = TranslationSession(
            snapshot_id="s1",
            prompt_hash="h1",
            request_count=3,
            chunk_index=2,
            metadata={"key": "val"},
        )
        assert session.snapshot_id == "s1"
        assert session.prompt_hash == "h1"
        assert session.request_count == 3
        assert session.chunk_index == 2

    def test_equality_excluding_timestamp(self):
        s1 = TranslationSession(session_id="abc", snapshot_id="s1")
        s2 = TranslationSession(session_id="abc", snapshot_id="s1")
        assert s1.session_id == s2.session_id
        assert s1.snapshot_id == s2.snapshot_id
        assert s1.request_count == s2.request_count
        assert s1.chunk_index == s2.chunk_index
        assert s1.prompt_hash == s2.prompt_hash
        assert s1.metadata == s2.metadata

    def test_different_session_id_not_equal(self):
        s1 = TranslationSession(session_id="abc")
        s2 = TranslationSession(session_id="def")
        assert s1 != s2


class TestRunStatus:
    def test_enum_values(self):
        assert RunStatus.CREATED.value == "CREATED"
        assert RunStatus.RUNNING.value == "RUNNING"
        assert RunStatus.PAUSED.value == "PAUSED"
        assert RunStatus.COMPLETED.value == "COMPLETED"
        assert RunStatus.FAILED.value == "FAILED"

    def test_str_enum(self):
        status = RunStatus.RUNNING
        assert status.value == "RUNNING"
        assert status == "RUNNING"

    def test_membership(self):
        valid = {"CREATED", "RUNNING", "PAUSED", "COMPLETED", "FAILED"}
        for s in RunStatus:
            assert s.value in valid


class TestRuntimeState:
    def test_initial_state(self):
        state = RuntimeState(session_id="s1")
        assert state.current_chunk == 0
        assert state.total_chunks == 0
        assert state.status == RunStatus.CREATED

    def test_valid_transition_created_to_running(self):
        state = RuntimeState(session_id="s1")
        assert state.can_transition_to(RunStatus.RUNNING) is True

    def test_valid_transition_running_to_paused(self):
        state = RuntimeState(session_id="s1", status=RunStatus.RUNNING)
        assert state.can_transition_to(RunStatus.PAUSED) is True

    def test_valid_transition_running_to_completed(self):
        state = RuntimeState(session_id="s1", status=RunStatus.RUNNING)
        assert state.can_transition_to(RunStatus.COMPLETED) is True

    def test_valid_transition_running_to_failed(self):
        state = RuntimeState(session_id="s1", status=RunStatus.RUNNING)
        assert state.can_transition_to(RunStatus.FAILED) is True

    def test_valid_transition_paused_to_running(self):
        state = RuntimeState(session_id="s1", status=RunStatus.PAUSED)
        assert state.can_transition_to(RunStatus.RUNNING) is True

    def test_invalid_transition_created_to_paused(self):
        state = RuntimeState(session_id="s1")
        assert state.can_transition_to(RunStatus.PAUSED) is False

    def test_invalid_transition_completed_to_anything(self):
        state = RuntimeState(session_id="s1", status=RunStatus.COMPLETED)
        for target in RunStatus:
            assert state.can_transition_to(target) is False

    def test_invalid_transition_failed_to_anything(self):
        state = RuntimeState(session_id="s1", status=RunStatus.FAILED)
        for target in RunStatus:
            assert state.can_transition_to(target) is False

    def test_transition_method(self):
        state = RuntimeState(session_id="s1")
        next_state = state.transition(RunStatus.RUNNING)
        assert next_state.status == RunStatus.RUNNING
        assert next_state != state

    def test_transition_raises_for_invalid(self):
        state = RuntimeState(session_id="s1", status=RunStatus.COMPLETED)
        with pytest.raises(RuntimeStateTransitionError) as exc:
            state.transition(RunStatus.RUNNING)
        assert "COMPLETED" in str(exc.value)
        assert "RUNNING" in str(exc.value)

    def test_transition_raises_for_created_to_completed(self):
        state = RuntimeState(session_id="s1")
        with pytest.raises(RuntimeStateTransitionError):
            state.transition(RunStatus.COMPLETED)

    def test_transition_updates_timestamps_on_running(self):
        state = RuntimeState(session_id="s1")
        before = utc_now_iso()
        next_state = state.transition(RunStatus.RUNNING)
        assert next_state.last_request >= before

    def test_transition_updates_timestamps_on_completed(self):
        state = RuntimeState(session_id="s1", status=RunStatus.RUNNING)
        before = utc_now_iso()
        next_state = state.transition(RunStatus.COMPLETED)
        assert next_state.last_response >= before

    def test_transition_preserves_chunk_counters(self):
        state = RuntimeState(session_id="s1", current_chunk=5, total_chunks=20)
        next_state = state.transition(RunStatus.RUNNING)
        assert next_state.current_chunk == 5
        assert next_state.total_chunks == 20

    def test_transition_with_kwargs(self):
        state = RuntimeState(session_id="s1")
        next_state = state.transition(RunStatus.RUNNING, current_chunk=3, total_chunks=15)
        assert next_state.current_chunk == 3
        assert next_state.total_chunks == 15
        assert next_state.status == RunStatus.RUNNING

    def test_full_workflow(self):
        state = RuntimeState(session_id="s1")
        assert state.status == RunStatus.CREATED

        state = state.transition(RunStatus.RUNNING)
        assert state.status == RunStatus.RUNNING

        state = state.transition(RunStatus.PAUSED)
        assert state.status == RunStatus.PAUSED

        state = state.transition(RunStatus.RUNNING)
        assert state.status == RunStatus.RUNNING

        state = state.transition(RunStatus.COMPLETED)
        assert state.status == RunStatus.COMPLETED


class TestSessionTrace:
    def test_create_trace(self):
        trace = SessionTrace(session_id="s1")
        assert trace.session_id == "s1"
        assert trace.entries == []
        assert trace.entry_count == 0

    def test_append_trace(self):
        trace = SessionTrace(session_id="s1")
        entry = TraceEntry(
            request_hash="req-hash",
            snapshot_id="snap-1",
            chunk=0,
        )
        updated = trace.append(entry)
        assert updated.entry_count == 1
        assert trace.entry_count == 0

    def test_append_multiple_entries(self):
        trace = SessionTrace(session_id="s1")
        e1 = TraceEntry(request_hash="h1", snapshot_id="s1", chunk=0)
        e2 = TraceEntry(request_hash="h2", snapshot_id="s1", chunk=1)
        e3 = TraceEntry(request_hash="h3", snapshot_id="s1", chunk=2)

        trace = trace.append(e1)
        trace = trace.append(e2)
        trace = trace.append(e3)

        assert trace.entry_count == 3
        assert trace.entries[0].request_hash == "h1"
        assert trace.entries[1].request_hash == "h2"
        assert trace.entries[2].request_hash == "h3"

    def test_deterministic_ordering(self):
        trace = SessionTrace(session_id="s1")
        entries = [
            TraceEntry(request_hash=f"h{i}", snapshot_id="s", chunk=i)
            for i in range(5)
        ]
        for e in entries:
            trace = trace.append(e)

        assert trace.entries == entries
        for i, entry in enumerate(trace.entries):
            assert entry.chunk == i

    def test_immutable(self):
        trace = SessionTrace(session_id="s1")
        with pytest.raises(FrozenInstanceError):
            trace.entries = []


class TestTraceEntry:
    def test_create_entry(self):
        entry = TraceEntry(
            request_hash="req-hash",
            snapshot_id="snap-1",
            chunk=3,
        )
        assert entry.request_hash == "req-hash"
        assert entry.snapshot_id == "snap-1"
        assert entry.chunk == 3
        assert entry.timestamp

    def test_timestamp_present(self):
        entry = TraceEntry(request_hash="h", snapshot_id="s", chunk=0)
        assert len(entry.timestamp) > 0

    def test_as_tuple(self):
        entry = TraceEntry(
            request_hash="req-hash",
            snapshot_id="snap-1",
            chunk=5,
        )
        tup = entry.as_tuple()
        assert tup[0] == "req-hash"
        assert tup[1] == "snap-1"
        assert tup[2] == 5
        assert tup[3] == entry.timestamp

    def test_immutable(self):
        entry = TraceEntry(request_hash="h", snapshot_id="s", chunk=0)
        with pytest.raises(FrozenInstanceError):
            entry.chunk = 99


class TestRunStatusTransitionMatrix:
    """Verify all 25 state transition combinations."""

    VALID = {
        (RunStatus.CREATED, RunStatus.RUNNING): True,
        (RunStatus.CREATED, RunStatus.FAILED): True,
        (RunStatus.RUNNING, RunStatus.PAUSED): True,
        (RunStatus.RUNNING, RunStatus.COMPLETED): True,
        (RunStatus.RUNNING, RunStatus.FAILED): True,
        (RunStatus.PAUSED, RunStatus.RUNNING): True,
        (RunStatus.PAUSED, RunStatus.COMPLETED): True,
        (RunStatus.PAUSED, RunStatus.FAILED): True,
    }

    def test_all_transitions(self):
        for src in RunStatus:
            state = RuntimeState(session_id="t", status=src)
            for tgt in RunStatus:
                expected = self.VALID.get((src, tgt), False)
                assert state.can_transition_to(tgt) == expected, f"{src.value} → {tgt.value}"


class TestDeterministicHash:
    def test_same_inputs_same_hash(self):
        h1 = _session_hash("a", "b")
        h2 = _session_hash("a", "b")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = _session_hash("a", "b")
        h2 = _session_hash("a", "c")
        assert h1 != h2

    def test_length(self):
        h = _session_hash("hello")
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


class TestGenerateSessionId:
    def test_returns_string(self):
        sid = _generate_session_id()
        assert isinstance(sid, str)
        assert len(sid) == 12

    def test_unique(self):
        ids = {_generate_session_id() for _ in range(100)}
        assert len(ids) == 100
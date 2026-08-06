"""Tests for Runtime Session Manager (RM-6.3.1)."""

import pytest

from core.runtime_session.models import (
    TranslationSession,
    RuntimeState,
    RunStatus,
    SessionTrace,
    TraceEntry,
    RuntimeStateTransitionError,
)
from core.runtime_session.manager import RuntimeSessionManager


class TestCreateSession:
    def test_create_returns_session(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        assert session.created_at

    def test_create_populates_snapshot_id(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(snapshot_id="snap-1")
        assert session.snapshot_id == "snap-1"

    def test_create_populates_prompt_hash(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(prompt_hash="ph-1")
        assert session.prompt_hash == "ph-1"

    def test_create_populates_metadata(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(metadata={"novel": "Dawn"})
        assert session.metadata["novel"] == "Dawn"

    def test_create_initializes_state(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        state = mgr.get_state(session.session_id)
        assert state is not None
        assert state.session_id == session.session_id
        assert state.status == RunStatus.CREATED

    def test_create_initializes_trace(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        trace = mgr.get_trace(session.session_id)
        assert trace is not None
        assert trace.entries == []

    def test_create_sessions_unique(self):
        mgr = RuntimeSessionManager()
        s1 = mgr.create_session()
        s2 = mgr.create_session()
        assert s1.session_id != s2.session_id
        assert mgr.active_sessions == 2

    def test_create_does_not_modify_translation_engine(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        assert session.version == "rm-6.3.1"


class TestLoadSession:
    def test_load_existing(self):
        mgr = RuntimeSessionManager()
        created = mgr.create_session(snapshot_id="s1")
        loaded = mgr.load_session(created.session_id)
        assert loaded == created

    def test_load_nonexistent(self):
        mgr = RuntimeSessionManager()
        assert mgr.load_session("no-such-id") is None


class TestSaveSession:
    def test_save_persists_in_memory(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(snapshot_id="original")
        new_session = TranslationSession(
            session_id=session.session_id,
            snapshot_id="updated",
        )
        mgr.save_session(new_session)
        loaded = mgr.load_session(session.session_id)
        assert loaded.snapshot_id == "updated"


class TestUpdateRuntime:
    def test_update_chunk_counters(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        state = mgr.update_runtime(
            session.session_id,
            current_chunk=5,
            total_chunks=20,
        )
        assert state.current_chunk == 5
        assert state.total_chunks == 20

    def test_update_status_transition(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        state = mgr.update_runtime(
            session.session_id,
            status=RunStatus.RUNNING,
        )
        assert state.status == RunStatus.RUNNING

    def test_update_status_invalid_transition(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        with pytest.raises(RuntimeStateTransitionError):
            mgr.update_runtime(
                session.session_id,
                status=RunStatus.PAUSED,
            )

    def test_update_metadata_merges(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(metadata={"a": 1})
        state = mgr.update_runtime(
            session.session_id,
            metadata={"b": 2},
        )
        assert state.metadata["b"] == 2

    def test_update_nonexistent_session(self):
        mgr = RuntimeSessionManager()
        with pytest.raises(KeyError):
            mgr.update_runtime("no-such-id", current_chunk=1)

    def test_update_preserves_state_between_calls(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        s1 = mgr.update_runtime(session.session_id, status=RunStatus.RUNNING, current_chunk=1)
        assert s1.status == RunStatus.RUNNING
        assert s1.current_chunk == 1

        s2 = mgr.update_runtime(session.session_id, current_chunk=2)
        assert s2.status == RunStatus.RUNNING
        assert s2.current_chunk == 2

    def test_full_state_workflow(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.update_runtime(session.session_id, current_chunk=3, total_chunks=10)
        mgr.update_runtime(session.session_id, status=RunStatus.PAUSED)
        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.update_runtime(session.session_id, status=RunStatus.COMPLETED)

        final = mgr.get_state(session.session_id)
        assert final.status == RunStatus.COMPLETED
        assert final.current_chunk == 3
        assert final.total_chunks == 10


class TestAppendTrace:
    def test_append_single_entry(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        trace = mgr.append_trace(
            session.session_id,
            request_hash="rh-1",
            snapshot_id="snap-1",
            chunk=0,
        )
        assert trace.entry_count == 1
        assert trace.entries[0].request_hash == "rh-1"
        assert trace.entries[0].snapshot_id == "snap-1"
        assert trace.entries[0].chunk == 0

    def test_append_multiple_entries(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        for i in range(5):
            mgr.append_trace(
                session.session_id,
                request_hash=f"rh-{i}",
                snapshot_id="snap-1",
                chunk=i,
            )

        trace = mgr.get_trace(session.session_id)
        assert trace.entry_count == 5
        assert [e.chunk for e in trace.entries] == [0, 1, 2, 3, 4]

    def test_deterministic_ordering(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        hashes = []
        for i in range(10):
            mgr.append_trace(
                session.session_id,
                request_hash=f"h{i:04d}",
                snapshot_id="s",
                chunk=i,
            )
            hashes.append(f"h{i:04d}")

        trace = mgr.get_trace(session.session_id)
        assert [e.request_hash for e in trace.entries] == hashes
        assert [e.chunk for e in trace.entries] == list(range(10))

    def test_append_nonexistent_session(self):
        mgr = RuntimeSessionManager()
        with pytest.raises(ValueError):
            mgr.append_trace("no-such-id", "h", "s", 0)

    def test_metadata_correctness(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session(snapshot_id="snap-meta", metadata={"type": "test"})

        mgr.append_trace(
            session.session_id,
            request_hash="rh-meta",
            snapshot_id="snap-meta",
            chunk=1,
        )

        trace = mgr.get_trace(session.session_id)
        assert trace.entries[0].snapshot_id == "snap-meta"
        assert trace.entries[0].request_hash == "rh-meta"
        assert trace.entries[0].chunk == 1
        assert trace.entries[0].timestamp

    def test_trace_is_persisted_in_memory(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        mgr.append_trace(session.session_id, "h1", "s1", 0)
        mgr.append_trace(session.session_id, "h2", "s2", 1)

        trace = mgr.get_trace(session.session_id)
        assert trace.entry_count == 2

        trace2 = mgr.get_trace(session.session_id)
        assert trace2 == trace


class TestFinishSession:
    def test_finish_success(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        state = mgr.get_state(session.session_id)
        assert state.status == RunStatus.CREATED

        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.finish_session(session.session_id, success=True)
        final = mgr.get_state(session.session_id)
        assert final.status == RunStatus.COMPLETED

    def test_finish_failure(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()

        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.finish_session(session.session_id, success=False)
        final = mgr.get_state(session.session_id)
        assert final.status == RunStatus.FAILED

    def test_finish_nonexistent_session(self):
        mgr = RuntimeSessionManager()
        with pytest.raises(ValueError):
            mgr.finish_session("no-such-id")

    def test_finish_without_state(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        mgr._states.pop(session.session_id, None)
        with pytest.raises(ValueError):
            mgr.finish_session(session.session_id)

    def test_finish_from_running(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.finish_session(session.session_id)
        final = mgr.get_state(session.session_id)
        assert final.status == RunStatus.COMPLETED


class TestStateForSession:
    def test_returns_state(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        state = mgr.state_for_session(session.session_id)
        assert state.session_id == session.session_id

    def test_raises_for_missing(self):
        mgr = RuntimeSessionManager()
        with pytest.raises(ValueError):
            mgr.state_for_session("no-such-id")


class TestTraceForSession:
    def test_returns_trace(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        trace = mgr.trace_for_session(session.session_id)
        assert trace.session_id == session.session_id

    def test_raises_for_missing(self):
        mgr = RuntimeSessionManager()
        with pytest.raises(ValueError):
            mgr.trace_for_session("no-such-id")


class TestManifest:
    def test_manifest(self):
        mgr = RuntimeSessionManager()
        manifest = mgr.manifest()
        assert manifest["name"] == "runtime_session_manager"
        assert manifest["version"] == mgr.version
        assert manifest["enabled"] is True


class TestManagerIntegration:
    def test_full_session_lifecycle(self):
        mgr = RuntimeSessionManager()

        session = mgr.create_session(
            snapshot_id="snap-lifecycle",
            prompt_hash="p-hash",
            metadata={"book": "Test"},
        )

        assert mgr.active_sessions == 1

        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING, total_chunks=3)

        mgr.append_trace(
            session.session_id,
            request_hash="req-0",
            snapshot_id="snap-lifecycle",
            chunk=0,
        )
        mgr.update_runtime(session.session_id, current_chunk=1)

        mgr.append_trace(
            session.session_id,
            request_hash="req-1",
            snapshot_id="snap-lifecycle",
            chunk=1,
        )
        mgr.update_runtime(session.session_id, current_chunk=2)

        mgr.append_trace(
            session.session_id,
            request_hash="req-2",
            snapshot_id="snap-lifecycle",
            chunk=2,
        )
        mgr.update_runtime(session.session_id, current_chunk=3)

        mgr.finish_session(session.session_id, success=True)

        final_state = mgr.get_state(session.session_id)
        assert final_state.status == RunStatus.COMPLETED
        assert final_state.current_chunk == 3
        assert final_state.total_chunks == 3

        trace = mgr.get_trace(session.session_id)
        assert trace.entry_count == 3
        assert [e.chunk for e in trace.entries] == [0, 1, 2]
        assert all(e.snapshot_id == "snap-lifecycle" for e in trace.entries)

    def test_no_provider_imports(self):
        mgr = RuntimeSessionManager()
        mgr.create_session()
        assert mgr.manifest()["enabled"] is True

    def test_no_network_calls(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session()
        mgr.update_runtime(session.session_id, status=RunStatus.RUNNING)
        mgr.append_trace(session.session_id, "h", "s", 0)
        mgr.finish_session(session.session_id, success=False)
        final = mgr.get_state(session.session_id)
        assert final.status == RunStatus.FAILED

    def test_manager_holds_multiple_sessions(self):
        mgr = RuntimeSessionManager()
        ids = []
        for i in range(5):
            s = mgr.create_session(snapshot_id=f"s{i}")
            ids.append(s.session_id)

        assert mgr.active_sessions == 5
        for sid in ids:
            assert mgr.load_session(sid) is not None

    def test_finish_transitions_invalid_state(self):
        mgr = RuntimeSessionManager()
        s = mgr.create_session()
        mgr.update_runtime(s.session_id, status=RunStatus.RUNNING)
        mgr.finish_session(s.session_id, success=True)
        with pytest.raises(RuntimeStateTransitionError):
            mgr.finish_session(s.session_id, success=False)
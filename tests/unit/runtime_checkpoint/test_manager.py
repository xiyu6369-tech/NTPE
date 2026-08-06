"""Tests for Runtime Checkpoint Manager (RM-6.3.2)."""

import pytest

from core.runtime_checkpoint.models import (
    CheckpointSnapshot,
    ProgressState,
    ProgressStatus,
    RequestManifest,
)
from core.runtime_checkpoint.manager import (
    RuntimeCheckpointManager,
    CheckpointNotFoundError,
    CheckpointSessionMismatchError,
    CheckpointIntegrityError,
)


class TestCreateCheckpoint:
    def test_create_basic(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="sid-1")
        assert cp.session_id == "sid-1"
        assert cp.checkpoint_id
        assert cp.snapshot_id
        assert cp.state_hash != ""
        assert mgr.total_checkpoints == 1

    def test_create_with_chunk_index(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1", chunk_index=5)
        assert cp.chunk_index == 5

    def test_create_with_progress(self):
        mgr = RuntimeCheckpointManager()
        progress = ProgressState(
            current_chunk=3,
            completed_chunks=2,
            total_chunks=10,
            status=ProgressStatus.ACTIVE,
        )
        cp = mgr.create_checkpoint(session_id="s1", progress=progress)
        assert cp.progress.current_chunk == 3
        assert cp.progress.completed_chunks == 2
        assert cp.progress.total_chunks == 10

    def test_create_with_manifest(self):
        mgr = RuntimeCheckpointManager()
        manifest = RequestManifest("rh", "ph", "sn", 3)
        cp = mgr.create_checkpoint(session_id="s1", manifest=manifest)
        assert cp.manifest.request_hash == "rh"
        assert cp.manifest.prompt_hash == "ph"

    def test_create_with_metadata(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1", metadata={"book": "Dawn"})
        assert cp.metadata["book"] == "Dawn"

    def test_create_multiple_sessions(self):
        mgr = RuntimeCheckpointManager()
        c1 = mgr.create_checkpoint(session_id="s1")
        c2 = mgr.create_checkpoint(session_id="s2")
        assert c1.session_id != c2.session_id
        assert mgr.active_sessions == 2
        assert mgr.total_checkpoints == 2

    def test_create_multiple_checkpoints_same_session(self):
        mgr = RuntimeCheckpointManager()
        c1 = mgr.create_checkpoint(session_id="s1", chunk_index=1)
        c2 = mgr.create_checkpoint(session_id="s1", chunk_index=2)
        assert c1.checkpoint_id != c2.checkpoint_id
        assert mgr.active_sessions == 1
        assert mgr.total_checkpoints == 2


class TestLoadCheckpoint:
    def test_load_existing(self):
        mgr = RuntimeCheckpointManager()
        created = mgr.create_checkpoint(session_id="s1")
        loaded = mgr.load_checkpoint("s1", created.checkpoint_id)
        assert loaded == created

    def test_load_nonexistent_session(self):
        mgr = RuntimeCheckpointManager()
        with pytest.raises(CheckpointNotFoundError):
            mgr.load_checkpoint("no-such", "cp-1")

    def test_load_nonexistent_checkpoint(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1")
        with pytest.raises(CheckpointNotFoundError):
            mgr.load_checkpoint("s1", "no-such-cp")


class TestValidateCheckpoint:
    def test_valid_checkpoint(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1")
        validated = mgr.validate_checkpoint("s1", cp.checkpoint_id)
        assert validated == cp

    def test_invalid_hash_detected(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1")
        corrupted = CheckpointSnapshot(
            checkpoint_id=cp.checkpoint_id,
            session_id="s1",
            chunk_index=999,
            progress=ProgressState(current_chunk=999),
            state_hash=cp.state_hash,
        )
        mgr._checkpoints["s1"][cp.checkpoint_id] = corrupted
        with pytest.raises(CheckpointIntegrityError):
            mgr.validate_checkpoint("s1", cp.checkpoint_id)


class TestRestoreSession:
    def test_restore_calls_callback(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1")
        captured = {}

        def restore_fn(cp_snap):
            captured["checkpoint"] = cp_snap

        result = mgr.restore_session("s1", cp.checkpoint_id, restore_fn)
        assert result == cp
        assert captured["checkpoint"] == cp

    def test_restore_invalid_fails(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1")
        corrupted = CheckpointSnapshot(
            checkpoint_id=cp.checkpoint_id,
            session_id="wrong",
            state_hash=cp.state_hash,
        )
        mgr._checkpoints["s1"][cp.checkpoint_id] = corrupted
        with pytest.raises(CheckpointSessionMismatchError):
            mgr.restore_session("s1", cp.checkpoint_id, lambda c: None)


class TestListCheckpoints:
    def test_list_empty(self):
        mgr = RuntimeCheckpointManager()
        assert mgr.list_checkpoints("s1") == []

    def test_list_ordering(self):
        mgr = RuntimeCheckpointManager()
        c1 = mgr.create_checkpoint(session_id="s1", chunk_index=1)
        c2 = mgr.create_checkpoint(session_id="s1", chunk_index=2)
        c3 = mgr.create_checkpoint(session_id="s1", chunk_index=3)
        listed = mgr.list_checkpoints("s1")
        assert len(listed) == 3
        assert listed[0].checkpoint_id == c1.checkpoint_id
        assert listed[1].checkpoint_id == c2.checkpoint_id
        assert listed[2].checkpoint_id == c3.checkpoint_id

    def test_list_no_session(self):
        mgr = RuntimeCheckpointManager()
        assert mgr.list_checkpoints("no-session") == []


class TestLatestCheckpoint:
    def test_latest_empty(self):
        mgr = RuntimeCheckpointManager()
        assert mgr.latest_checkpoint("s1") is None

    def test_latest_returns_last(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1", chunk_index=1)
        mgr.create_checkpoint(session_id="s1", chunk_index=2)
        c3 = mgr.create_checkpoint(session_id="s1", chunk_index=3)
        latest = mgr.latest_checkpoint("s1")
        assert latest == c3


class TestDeleteCheckpoint:
    def test_delete_existing(self):
        mgr = RuntimeCheckpointManager()
        cp = mgr.create_checkpoint(session_id="s1")
        mgr.delete_checkpoint("s1", cp.checkpoint_id)
        assert mgr.total_checkpoints == 0
        assert mgr.active_sessions == 0

    def test_delete_nonexistent(self):
        mgr = RuntimeCheckpointManager()
        with pytest.raises(CheckpointNotFoundError):
            mgr.delete_checkpoint("s1", "no-such")

    def test_delete_one_of_many(self):
        mgr = RuntimeCheckpointManager()
        c1 = mgr.create_checkpoint(session_id="s1")
        c2 = mgr.create_checkpoint(session_id="s1")
        mgr.delete_checkpoint("s1", c1.checkpoint_id)
        assert mgr.total_checkpoints == 1
        assert mgr.active_sessions == 1
        loaded = mgr.load_checkpoint("s1", c2.checkpoint_id)
        assert loaded == c2


class TestRecover:
    def test_recover_from_latest(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1", chunk_index=1)
        mgr.create_checkpoint(session_id="s1", chunk_index=2)
        captured = []
        result = mgr.recover("s1", lambda c: captured.append(c))
        assert result is not None
        assert result.chunk_index == 2
        assert len(captured) == 1

    def test_recover_empty_session(self):
        mgr = RuntimeCheckpointManager()
        captured = []
        result = mgr.recover("s1", lambda c: captured.append(c))
        assert result is None
        assert len(captured) == 0

    def test_recover_triggered_after_multiple_checkpoints(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1", chunk_index=1)
        mgr.create_checkpoint(session_id="s1", chunk_index=2)
        mgr.create_checkpoint(session_id="s1", chunk_index=3)
        latest = mgr.recover("s1", lambda c: None)
        assert latest.chunk_index == 3


class TestRecoveryFlow:
    def test_normal_progression(self):
        mgr = RuntimeCheckpointManager()
        cp1 = mgr.create_checkpoint(session_id="s1", chunk_index=1)
        cp2 = mgr.create_checkpoint(session_id="s1", chunk_index=2)
        cp3 = mgr.create_checkpoint(session_id="s1", chunk_index=3)
        assert mgr.total_checkpoints == 3
        restored = mgr.restore_session("s1", cp3.checkpoint_id, lambda c: None)
        assert restored.chunk_index == 3

    def test_failure_and_recovery(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1", chunk_index=1)
        mgr.create_checkpoint(session_id="s1", chunk_index=2)
        restored_state = {}
        def restore(cp):
            restored_state["chunk"] = cp.chunk_index

        mgr.recover("s1", restore)
        assert restored_state["chunk"] == 2

    def test_recovery_skips_corrupted(self):
        mgr = RuntimeCheckpointManager()
        c1 = mgr.create_checkpoint(session_id="s1", chunk_index=1)
        c2 = mgr.create_checkpoint(session_id="s1", chunk_index=2)
        corrupted = CheckpointSnapshot(
            checkpoint_id=c2.checkpoint_id,
            session_id="s1",
            chunk_index=99,
            state_hash=c2.state_hash,
        )
        mgr._checkpoints["s1"][c2.checkpoint_id] = corrupted
        with pytest.raises(CheckpointIntegrityError):
            mgr.recover("s1", lambda c: None)


class TestManagerIntegration:
    def test_full_checkpoint_lifecycle(self):
        mgr = RuntimeCheckpointManager()

        cp1 = mgr.create_checkpoint(
            session_id="lifecycle-session",
            chunk_index=1,
            metadata={"stage": "start"},
        )
        assert mgr.total_checkpoints == 1

        cp2 = mgr.create_checkpoint(
            session_id="lifecycle-session",
            chunk_index=2,
            metadata={"stage": "middle"},
        )
        assert mgr.total_checkpoints == 2

        loaded = mgr.load_checkpoint("lifecycle-session", cp1.checkpoint_id)
        assert loaded.metadata["stage"] == "start"

        validated = mgr.validate_checkpoint("lifecycle-session", cp2.checkpoint_id)
        assert validated.chunk_index == 2

        mgr.delete_checkpoint("lifecycle-session", cp1.checkpoint_id)
        assert mgr.total_checkpoints == 1
        assert mgr.active_sessions == 1

        mgr.delete_checkpoint("lifecycle-session", cp2.checkpoint_id)
        assert mgr.total_checkpoints == 0
        assert mgr.active_sessions == 0

    def test_no_provider_imports(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1")
        assert mgr.total_checkpoints == 1

    def test_no_network_calls(self):
        mgr = RuntimeCheckpointManager()
        mgr.create_checkpoint(session_id="s1")
        mgr.create_checkpoint(session_id="s1", chunk_index=5)
        mgr.recover("s1", lambda c: None)
        assert mgr.total_checkpoints == 2
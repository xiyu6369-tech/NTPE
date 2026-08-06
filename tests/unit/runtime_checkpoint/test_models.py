"""Tests for Runtime Checkpoint domain models (RM-6.3.2)."""

from dataclasses import FrozenInstanceError

import pytest

from core.runtime_checkpoint.models import (
    CheckpointSnapshot,
    ProgressState,
    ProgressStatus,
    RequestManifest,
    _checkpoint_hash,
    _generate_checkpoint_id,
    _generate_snapshot_id,
    utc_now_iso,
)


class TestProgressState:
    def test_defaults(self):
        ps = ProgressState()
        assert ps.current_chunk == 0
        assert ps.completed_chunks == 0
        assert ps.total_chunks == 0
        assert ps.status == ProgressStatus.ACTIVE

    def test_with_values(self):
        ps = ProgressState(
            current_chunk=5,
            completed_chunks=3,
            total_chunks=20,
            status=ProgressStatus.PAUSED,
        )
        assert ps.current_chunk == 5
        assert ps.completed_chunks == 3
        assert ps.total_chunks == 20
        assert ps.status == ProgressStatus.PAUSED

    def test_immutable(self):
        ps = ProgressState(current_chunk=5)
        with pytest.raises(FrozenInstanceError):
            ps.current_chunk = 10


class TestProgressStatus:
    def test_enum_values(self):
        assert ProgressStatus.ACTIVE.value == "ACTIVE"
        assert ProgressStatus.PAUSED.value == "PAUSED"
        assert ProgressStatus.COMPLETED.value == "COMPLETED"
        assert ProgressStatus.FAILED.value == "FAILED"

    def test_str_equality(self):
        assert ProgressStatus.ACTIVE == "ACTIVE"
        assert ProgressStatus.PAUSED == "PAUSED"


class TestRequestManifest:
    def test_create(self):
        rm = RequestManifest(
            request_hash="req-hash-1",
            prompt_hash="prompt-hash-1",
            snapshot_id="snap-1",
            chunk_index=3,
        )
        assert rm.request_hash == "req-hash-1"
        assert rm.prompt_hash == "prompt-hash-1"
        assert rm.snapshot_id == "snap-1"
        assert rm.chunk_index == 3

    def test_immutable(self):
        rm = RequestManifest("rh", "ph", "si", 0)
        with pytest.raises(FrozenInstanceError):
            rm.chunk_index = 9

    def test_no_api_payload(self):
        rm = RequestManifest("rh", "ph", "si", 0)
        assert not hasattr(rm, "provider_payload")
        assert not hasattr(rm, "translated_text")
        assert not hasattr(rm, "api_response")


class TestCheckpointSnapshot:
    def test_defaults(self):
        cp = CheckpointSnapshot()
        assert cp.checkpoint_id
        assert len(cp.checkpoint_id) == 12
        assert cp.session_id == ""
        assert cp.snapshot_id
        assert cp.snapshot_id.startswith("snap-")
        assert cp.chunk_index == 0
        assert cp.created_at
        assert cp.state_hash == ""
        assert cp.version == "rm-6.3.2"

    def test_with_values(self):
        progress = ProgressState(current_chunk=3, completed_chunks=2, total_chunks=10)
        manifest = RequestManifest("rh", "ph", "sn", 3)
        cp = CheckpointSnapshot(
            session_id="sid-1",
            chunk_index=3,
            progress=progress,
            manifest=manifest,
            metadata={"book": "Test"},
        )
        assert cp.session_id == "sid-1"
        assert cp.chunk_index == 3
        assert cp.progress == progress
        assert cp.manifest == manifest
        assert cp.metadata["book"] == "Test"

    def test_immutable(self):
        cp = CheckpointSnapshot(session_id="s1")
        with pytest.raises(FrozenInstanceError):
            cp.session_id = "changed"

    def test_compute_hash_deterministic(self):
        cp = CheckpointSnapshot(session_id="s1", chunk_index=5)
        h1 = cp.compute_hash()
        h2 = cp.compute_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_compute_hash_differs_per_checkpoint(self):
        cp1 = CheckpointSnapshot(session_id="s1", chunk_index=1)
        cp2 = CheckpointSnapshot(session_id="s1", chunk_index=2)
        assert cp1.compute_hash() != cp2.compute_hash()

    def test_compute_hash_excludes_created_at(self):
        cp = CheckpointSnapshot(session_id="s1", chunk_index=5)
        h1 = cp.compute_hash()
        cp2 = CheckpointSnapshot(
            checkpoint_id=cp.checkpoint_id,
            session_id="s1",
            snapshot_id=cp.snapshot_id,
            chunk_index=5,
            progress=cp.progress,
            manifest=cp.manifest,
            metadata=cp.metadata,
        )
        assert cp2.created_at != cp.created_at
        assert cp2.compute_hash() == h1

    def test_with_hash(self):
        cp = CheckpointSnapshot(session_id="s1")
        assert cp.state_hash == ""
        cp_hashed = cp.with_hash()
        assert cp_hashed.state_hash != ""
        assert len(cp_hashed.state_hash) == 64

    def test_with_hash_roundtrip(self):
        cp = CheckpointSnapshot(session_id="s1", chunk_index=5)
        cp_hashed = cp.with_hash()
        computed = cp_hashed.compute_hash()
        assert cp_hashed.state_hash == computed

    def test_with_hash_preserves_fields(self):
        cp = CheckpointSnapshot(
            session_id="s1",
            chunk_index=3,
            metadata={"key": "val"},
        )
        cp_hashed = cp.with_hash()
        assert cp_hashed.session_id == "s1"
        assert cp_hashed.chunk_index == 3
        assert cp_hashed.metadata == {"key": "val"}

    def test_compute_hash_includes_manifest(self):
        manifest = RequestManifest("rh", "ph", "snap-a", 5)
        cp = CheckpointSnapshot(session_id="s1", manifest=manifest)
        h1 = cp.compute_hash()
        manifest2 = RequestManifest("rh2", "ph", "snap-a", 5)
        cp2 = CheckpointSnapshot(
            checkpoint_id=cp.checkpoint_id,
            session_id="s1",
            manifest=manifest2,
        )
        assert cp2.compute_hash() != h1


class TestSerialization:
    def test_progress_state_default_repr(self):
        ps = ProgressState()
        assert repr(ps)

    def test_checkpoint_snapshot_default_repr(self):
        cp = CheckpointSnapshot(session_id="s1")
        assert repr(cp)

    def test_request_manifest_default_repr(self):
        rm = RequestManifest("rh", "ph", "sn", 0)
        assert repr(rm)


class TestDeterministicHash:
    def test_same_inputs_same_hash(self):
        h1 = _checkpoint_hash("a", "b")
        h2 = _checkpoint_hash("a", "b")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = _checkpoint_hash("a", "b")
        h2 = _checkpoint_hash("a", "c")
        assert h1 != h2

    def test_length(self):
        h = _checkpoint_hash("hello")
        assert len(h) == 64


class TestUtcNowIso:
    def test_returns_string(self):
        ts = utc_now_iso()
        assert isinstance(ts, str)

    def test_contains_t(self):
        ts = utc_now_iso()
        assert "T" in ts


class TestGenerateCheckpointId:
    def test_returns_string(self):
        cid = _generate_checkpoint_id()
        assert isinstance(cid, str)
        assert len(cid) == 12

    def test_unique(self):
        ids = {_generate_checkpoint_id() for _ in range(100)}
        assert len(ids) == 100


class TestGenerateSnapshotId:
    def test_returns_string(self):
        sid = _generate_snapshot_id()
        assert isinstance(sid, str)
        assert sid.startswith("snap-")

    def test_unique(self):
        ids = {_generate_snapshot_id() for _ in range(100)}
        assert len(ids) == 100
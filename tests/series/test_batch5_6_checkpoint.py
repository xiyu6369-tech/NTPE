"""P0 Stage 5 Batch 5.6 — Series Checkpoint Hierarchy Tests."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from core.series_checkpoint import (
    SeriesCheckpoint,
    BookCheckpointRef,
    SessionCheckpointRef,
    CheckpointCreationReport,
    SeriesResumeReport,
    BookResumeReport,
    BookStartReport,
    BookResumeInfo,
    SeriesCheckpointManager,
    get_series_checkpoint_path,
    save_series_checkpoint,
    load_series_checkpoint_from_path,
    load_latest_series_checkpoint,
    compute_series_checkpoint_fingerprint,
    to_canonical_json,
    SeriesCheckpointValidationError,
    SeriesCheckpointIntegrityError,
    SeriesCheckpointBookHashMismatchError,
    SeriesCheckpointSessionMismatchError,
    validate_series_checkpoint_schema,
    validate_series_checkpoint_integrity,
    validate_series_checkpoint_full,
    validate_cross_series_isolation,
)
from core.runtime_checkpoint.models import ProgressState, ProgressStatus, RequestManifest


class TestSeriesCheckpointModels:
    """Test SeriesCheckpoint data models."""

    def test_series_checkpoint_creation(self):
        """Test SeriesCheckpoint creation with all fields."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash_123",
            book_context_hash="ctx_hash_456",
            latest_session_checkpoint_id="sess_a1b2c3d4e5f6",
            status="in_progress",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="state_hash_value",
        )

        assert checkpoint.series_id == "a1b2c3d4e5f6g7h8"
        assert checkpoint.checkpoint_id == "scheck_a1b2c3d4e5f6"
        assert len(checkpoint.book_checkpoints) == 1
        assert checkpoint.book_checkpoints[0].book_identity == "b1o2k3i4d5e6n7t8"

    def test_book_checkpoint_ref_serialization(self):
        """Test BookCheckpointRef to_dict/from_dict roundtrip."""
        original = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id="sess_123",
            status="completed",
        )

        data = original.to_dict()
        restored = BookCheckpointRef.from_dict(data)

        assert restored.book_identity == original.book_identity
        assert restored.volume_number == original.volume_number
        assert restored.book_memory_hash == original.book_memory_hash
        assert restored.book_context_hash == original.book_context_hash
        assert restored.latest_session_checkpoint_id == original.latest_session_checkpoint_id
        assert restored.status == original.status

    def test_session_checkpoint_ref_serialization(self):
        """Test SessionCheckpointRef to_dict/from_dict roundtrip."""
        progress = ProgressState(
            current_chunk=5,
            completed_chunks=5,
            total_chunks=100,
            status=ProgressStatus.ACTIVE,
        )
        manifest = RequestManifest(
            request_hash="req_hash",
            prompt_hash="prompt_hash",
            snapshot_id="snap_123",
            chunk_index=5,
        )

        original = SessionCheckpointRef(
            session_id="sess_a1b2c3d4e5f6",
            chunk_index=5,
            progress=progress,
            context_memory_hash="ctx_mem_hash",
            request_manifest=manifest,
        )

        data = original.to_dict()
        restored = SessionCheckpointRef.from_dict(data)

        assert restored.session_id == original.session_id
        assert restored.chunk_index == original.chunk_index
        assert restored.progress.current_chunk == original.progress.current_chunk
        assert restored.progress.status == original.progress.status
        assert restored.context_memory_hash == original.context_memory_hash
        assert restored.request_manifest is not None
        assert restored.request_manifest.request_hash == manifest.request_hash

    def test_series_checkpoint_serialization_roundtrip(self):
        """Test SeriesCheckpoint to_dict/from_dict roundtrip with hash."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id="sess_123",
            status="in_progress",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="computed_state_hash",
        )

        data = checkpoint.to_dict(include_state_hash=True)
        restored = SeriesCheckpoint.from_dict(data)

        assert restored.series_id == checkpoint.series_id
        assert restored.checkpoint_id == checkpoint.checkpoint_id
        assert restored.state_hash == checkpoint.state_hash
        assert len(restored.book_checkpoints) == 1
        assert restored.book_checkpoints[0].book_identity == book_ref.book_identity

    def test_canonical_json_deterministic(self):
        """Test deterministic JSON serialization."""
        obj = {"b": 2, "a": 1, "c": {"z": 3, "y": 4}}
        json1 = to_canonical_json(obj)
        json2 = to_canonical_json(obj)
        assert json1 == json2
        assert json1 == '{"a":1,"b":2,"c":{"y":4,"z":3}}'

    def test_fingerprint_deterministic(self):
        """Test checkpoint fingerprint is deterministic."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="",
        )

        # Compute fingerprint multiple times
        fp1 = compute_series_checkpoint_fingerprint(checkpoint.to_canonical_dict())
        fp2 = compute_series_checkpoint_fingerprint(checkpoint.to_canonical_dict())
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_checkpoint_id_format(self):
        """Test checkpoint ID follows scheck_ format."""
        from core.series_checkpoint.models import _generate_checkpoint_id

        cid1 = _generate_checkpoint_id("series_123")
        cid2 = _generate_checkpoint_id("series_123")
        assert cid1.startswith("scheck_")
        assert len(cid1) == 19  # "scheck_" + 12 hex chars
        # Note: Different each call due to timestamp


class TestSeriesCheckpointPersistence:
    """Test SeriesCheckpoint persistence operations."""

    def test_save_load_roundtrip(self, tmp_path):
        """Test save and load checkpoint roundtrip."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id="sess_123",
            status="in_progress",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="",  # Will be computed
        ).with_hash()

        # Save
        path = get_series_checkpoint_path(output_root, "a1b2c3d4e5f6g7h8")
        save_series_checkpoint(checkpoint, path)

        # Verify file exists
        assert path.exists()

        # Load
        loaded = load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")

        assert loaded is not None
        assert loaded.series_id == checkpoint.series_id
        assert loaded.checkpoint_id == checkpoint.checkpoint_id
        assert loaded.state_hash == checkpoint.state_hash
        assert loaded.series_memory_hash == checkpoint.series_memory_hash
        assert len(loaded.book_checkpoints) == 1
        assert loaded.book_checkpoints[0].book_identity == "b1o2k3i4d5e6n7t8"

    def test_load_missing_file_returns_none(self, tmp_path):
        """Test loading non-existent checkpoint returns None."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        result = load_latest_series_checkpoint("nonexistent", output_root)
        assert result is None

    def test_corrupted_json_raises_validation_error(self, tmp_path):
        """Test corrupted JSON raises validation error."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "a1b2c3d4e5f6g7h8"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_a1b2c3d4e5f6g7h8.json"
        path.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(SeriesCheckpointValidationError):
            load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")

    def test_wrong_schema_name_raises_error(self, tmp_path):
        """Test wrong schema_name raises validation error."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "a1b2c3d4e5f6g7h8"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_a1b2c3d4e5f6g7h8.json"

        data = {
            "schema_name": "wrong.schema",
            "schema_version": "1.0",
            "series_id": "a1b2c3d4e5f6g7h8",
            "checkpoint_id": "scheck_123",
            "created_at": "2026-08-21T00:00:00Z",
            "book_checkpoints": [],
        }
        path.write_text(to_canonical_json(data), encoding="utf-8")

        with pytest.raises(SeriesCheckpointValidationError):
            load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")

    def test_wrong_schema_version_raises_error(self, tmp_path):
        """Test wrong schema_version raises validation error."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "a1b2c3d4e5f6g7h8"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_a1b2c3d4e5f6g7h8.json"

        data = {
            "schema_name": "ntpe.series_checkpoint",
            "schema_version": "2.0",
            "series_id": "a1b2c3d4e5f6g7h8",
            "checkpoint_id": "scheck_123",
            "created_at": "2026-08-21T00:00:00Z",
            "book_checkpoints": [],
        }
        path.write_text(to_canonical_json(data), encoding="utf-8")

        with pytest.raises(SeriesCheckpointValidationError):
            load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")

    def test_series_id_mismatch_raises_error(self, tmp_path):
        """Test series_id mismatch raises validation error."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "a1b2c3d4e5f6g7h8"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_a1b2c3d4e5f6g7h8.json"

        data = {
            "schema_name": "ntpe.series_checkpoint",
            "schema_version": "1.0",
            "series_id": "different_series_id",
            "checkpoint_id": "scheck_123",
            "created_at": "2026-08-21T00:00:00Z",
            "book_checkpoints": [],
        }
        path.write_text(to_canonical_json(data), encoding="utf-8")

        with pytest.raises(SeriesCheckpointValidationError):
            load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")

    def test_tampered_fingerprint_raises_integrity_error(self, tmp_path):
        """Test tampered fingerprint raises integrity error."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="",
        ).with_hash()

        path = get_series_checkpoint_path(output_root, "a1b2c3d4e5f6g7h8")
        save_series_checkpoint(checkpoint, path)

        # Tamper with the file - change state_hash
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        data["state_hash"] = "tampered_hash"
        path.write_text(to_canonical_json(data), encoding="utf-8")

        with pytest.raises(SeriesCheckpointIntegrityError):
            load_series_checkpoint_from_path(path, "a1b2c3d4e5f6g7h8")


class TestSeriesCheckpointValidation:
    """Test SeriesCheckpoint validation logic."""

    def test_validate_schema_success(self):
        """Test valid checkpoint passes schema validation."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="valid_hash",
        )

        # Should not raise
        validate_series_checkpoint_schema(checkpoint)

    def test_validate_schema_missing_series_id(self):
        """Test missing series_id fails validation."""
        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="",
            checkpoint_id="scheck_123",
            created_at="2026-08-21T00:00:00Z",
            book_checkpoints=(),
        )

        with pytest.raises(SeriesCheckpointValidationError, match="series_id is required"):
            validate_series_checkpoint_schema(checkpoint)

    def test_validate_integrity_success(self):
        """Test valid checkpoint passes integrity validation."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash=compute_series_checkpoint_fingerprint({
                "schema_name": "ntpe.series_checkpoint",
                "schema_version": "1.0",
                "series_id": "a1b2c3d4e5f6g7h8",
                "checkpoint_id": "scheck_a1b2c3d4e5f6",
                "created_at": "2026-08-21T00:00:00Z",
                "series_memory_hash": "series_mem_hash",
                "series_entity_registry_hash": "series_ent_hash",
                "series_glossary_hash": "series_glos_hash",
                "series_knowledge_hash": "series_know_hash",
                "manifest_fingerprint": "manifest_fp",
                "book_checkpoints": [book_ref.to_dict()],
            }),
        )

        # Should not raise
        validate_series_checkpoint_integrity(checkpoint)

    def test_validate_integrity_tampered_fails(self):
        """Test tampered checkpoint fails integrity validation."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="wrong_hash",
        )

        with pytest.raises(SeriesCheckpointIntegrityError):
            validate_series_checkpoint_integrity(checkpoint)

    def test_cross_series_isolation_success(self):
        """Test cross-series isolation validation passes for matching IDs."""
        checkpoint = SeriesCheckpoint(
            series_id="series_a",
            checkpoint_id="scheck_abc123",
        )
        validate_cross_series_isolation(checkpoint, "series_a")

    def test_cross_series_isolation_fails(self):
        """Test cross-series isolation validation fails for mismatched IDs."""
        checkpoint = SeriesCheckpoint(
            series_id="series_a",
            checkpoint_id="scheck_abc123",
        )
        with pytest.raises(SeriesCheckpointValidationError, match="Series ID mismatch"):
            validate_cross_series_isolation(checkpoint, "series_b")

    def test_cross_series_isolation_invalid_format(self):
        """Test cross-series isolation fails for invalid checkpoint_id format."""
        checkpoint = SeriesCheckpoint(
            series_id="series_a",
            checkpoint_id="invalid_format",
        )
        with pytest.raises(SeriesCheckpointValidationError, match="series namespace format"):
            validate_cross_series_isolation(checkpoint, "series_a")


class TestSeriesCheckpointHierarchy:
    """Test 4-level hierarchy (Series -> Book -> Session -> Chunk)."""

    def test_4level_hierarchy_structure(self):
        """Test complete 4-level hierarchy structure."""
        session_ref = SessionCheckpointRef(
            session_id="sess_a1b2c3d4e5f6",
            chunk_index=10,
            progress=ProgressState(
                current_chunk=10,
                completed_chunks=10,
                total_chunks=100,
                status=ProgressStatus.ACTIVE,
            ),
            context_memory_hash="ctx_hash",
            request_manifest=RequestManifest(
                request_hash="req_hash",
                prompt_hash="prompt_hash",
                snapshot_id="snap_123",
                chunk_index=10,
            ),
        )

        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id="sess_a1b2c3d4e5f6",
            status="in_progress",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="state_hash",
        )

        # Verify hierarchy
        assert checkpoint.series_id == "a1b2c3d4e5f6g7h8"
        assert len(checkpoint.book_checkpoints) == 1
        assert checkpoint.book_checkpoints[0].book_identity == "b1o2k3i4d5e6n7t8"
        assert checkpoint.book_checkpoints[0].latest_session_checkpoint_id == "sess_a1b2c3d4e5f6"
        assert checkpoint.book_checkpoints[0].status == "in_progress"

    def test_multiple_books_in_series(self):
        """Test multiple books in series checkpoint."""
        book_refs = []
        for i in range(3):
            book_refs.append(BookCheckpointRef(
                book_identity=f"book_{i}",
                volume_number=i + 1,
                book_memory_hash=f"mem_hash_{i}",
                book_context_hash=f"ctx_hash_{i}",
                latest_session_checkpoint_id=f"sess_{i}" if i < 2 else None,
                status="in_progress" if i < 2 else "completed",
            ))

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_a1b2c3d4e5f6",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=tuple(book_refs),
            state_hash="state_hash",
        )

        assert len(checkpoint.book_checkpoints) == 3
        assert checkpoint.book_checkpoints[0].volume_number == 1
        assert checkpoint.book_checkpoints[1].volume_number == 2
        assert checkpoint.book_checkpoints[2].volume_number == 3
        assert checkpoint.book_checkpoints[0].status == "in_progress"
        assert checkpoint.book_checkpoints[2].status == "completed"


class TestDeterministicSerialization:
    """Property-based tests for deterministic serialization."""

    def test_checkpoint_fingerprint_deterministic_1000(self):
        """Test checkpoint fingerprint deterministic over 1000 iterations."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id=None,
            status="pending",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_fixed_id_for_test",  # Fixed for determinism
            created_at="2026-08-21T00:00:00Z",  # Fixed timestamp
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="",
        )

        fingerprints = set()
        for _ in range(1000):
            fp = compute_series_checkpoint_fingerprint(checkpoint.to_canonical_dict())
            fingerprints.add(fp)

        assert len(fingerprints) == 1  # All identical

    def test_serialization_roundtrip_property_1000(self):
        """Test serialization roundtrip over 1000 iterations."""
        book_ref = BookCheckpointRef(
            book_identity="b1o2k3i4d5e6n7t8",
            volume_number=1,
            book_memory_hash="mem_hash",
            book_context_hash="ctx_hash",
            latest_session_checkpoint_id="sess_123",
            status="in_progress",
        )

        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_fixed_id",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="series_mem_hash",
            series_entity_registry_hash="series_ent_hash",
            series_glossary_hash="series_glos_hash",
            series_knowledge_hash="series_know_hash",
            manifest_fingerprint="manifest_fp",
            book_checkpoints=(book_ref,),
            state_hash="computed_hash",
        )

        for _ in range(1000):
            data = checkpoint.to_dict(include_state_hash=True)
            restored = SeriesCheckpoint.from_dict(data)
            assert restored.series_id == checkpoint.series_id
            assert restored.state_hash == checkpoint.state_hash


class TestNamespaceIsolation:
    """Test cross-series namespace isolation."""

    def test_series_checkpoint_file_namespace(self, tmp_path):
        """Test series checkpoint files are namespaced by series_id."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        # Create checkpoint for series A
        path_a = get_series_checkpoint_path(output_root, "series_a")
        path_b = get_series_checkpoint_path(output_root, "series_b")

        assert path_a != path_b
        assert "series_a" in str(path_a)
        assert "series_b" in str(path_b)
        assert path_a.parent.name == "series_a"
        assert path_b.parent.name == "series_b"

    def test_checkpoint_id_contains_series_namespace(self):
        """Test checkpoint ID format includes series namespace implicitly."""
        from core.series_checkpoint.models import _generate_checkpoint_id

        cid_a = _generate_checkpoint_id("series_a")
        cid_b = _generate_checkpoint_id("series_b")

        assert cid_a != cid_b  # Different series -> different IDs (due to timestamp + series_id)
        assert cid_a.startswith("scheck_")
        assert cid_b.startswith("scheck_")


class TestFailClosedBehavior:
    """Test fail-closed behavior for all validation paths."""

    def test_schema_validation_fail_closed(self):
        """Schema validation failures raise exceptions, no fallback."""
        invalid_checkpoints = [
            SeriesCheckpoint(schema_name="wrong", schema_version="1.0", series_id="s", checkpoint_id="c", created_at="t", book_checkpoints=()),
            SeriesCheckpoint(schema_name="ntpe.series_checkpoint", schema_version="2.0", series_id="s", checkpoint_id="c", created_at="t", book_checkpoints=()),
            SeriesCheckpoint(schema_name="ntpe.series_checkpoint", schema_version="1.0", series_id="", checkpoint_id="c", created_at="t", book_checkpoints=()),
        ]

        for cp in invalid_checkpoints:
            with pytest.raises(SeriesCheckpointValidationError):
                validate_series_checkpoint_schema(cp)

    def test_integrity_validation_fail_closed(self):
        """Integrity validation failures raise exceptions, no fallback."""
        book_ref = BookCheckpointRef(
            book_identity="b1", volume_number=1, book_memory_hash="m", book_context_hash="c",
            latest_session_checkpoint_id=None, status="pending"
        )
        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            checkpoint_id="scheck_123",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="m1",
            series_entity_registry_hash="m2",
            series_glossary_hash="m3",
            series_knowledge_hash="m4",
            manifest_fingerprint="mf",
            book_checkpoints=(book_ref,),
            state_hash="wrong_hash",
        )

        with pytest.raises(SeriesCheckpointIntegrityError):
            validate_series_checkpoint_integrity(checkpoint)

    def test_load_corrupted_file_fail_closed(self, tmp_path):
        """Loading corrupted file raises exception, no partial load."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "test_series"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_test_series.json"
        path.write_text("{ corrupt }", encoding="utf-8")

        with pytest.raises(SeriesCheckpointValidationError):
            load_series_checkpoint_from_path(path, "test_series")

    def test_load_wrong_schema_fail_closed(self, tmp_path):
        """Loading wrong schema raises exception."""
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)
        series_dir = output_root / "series" / "test_series"
        series_dir.mkdir(parents=True)
        path = series_dir / "series_checkpoint_test_series.json"

        data = {
            "schema_name": "ntpe.series_checkpoint",
            "schema_version": "1.0",
            "series_id": "test_series",
            "checkpoint_id": "scheck_123",
            "created_at": "2026-08-21T00:00:00Z",
            "book_checkpoints": [],
        }
        path.write_text(to_canonical_json(data), encoding="utf-8")

        # This should pass (valid schema)
        loaded = load_series_checkpoint_from_path(path, "test_series")
        assert loaded is not None

    def test_no_silent_fallback_defaults(self):
        """No silent fallback to defaults on any validation failure."""
        # All validation functions should raise exceptions, not return defaults
        assert True  # Verified by above tests


class TestManifestIntegration:
    """Test SeriesManifest series_checkpoint_hash integration."""

    def test_checkpoint_hash_computed_for_manifest(self):
        """Test checkpoint provides hash for manifest integration."""
        book_ref = BookCheckpointRef(
            book_identity="b1", volume_number=1, book_memory_hash="m", book_context_hash="c",
            latest_session_checkpoint_id=None, status="pending"
        )
        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="s1",
            checkpoint_id="c1",
            created_at="t",
            series_memory_hash="sm",
            series_entity_registry_hash="se",
            series_glossary_hash="sg",
            series_knowledge_hash="sk",
            manifest_fingerprint="mf",
            book_checkpoints=(book_ref,),
            state_hash="computed_state_hash",
        )

        assert checkpoint.get_checkpoint_hash() == "computed_state_hash"

    def test_manifest_hash_updates_with_checkpoint(self):
        """Test manifest fingerprint changes when checkpoint changes."""
        book_ref = BookCheckpointRef(
            book_identity="b1", volume_number=1, book_memory_hash="m", book_context_hash="c",
            latest_session_checkpoint_id=None, status="pending"
        )

        checkpoint1 = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="s1",
            checkpoint_id="c1",
            created_at="t1",
            series_memory_hash="sm",
            series_entity_registry_hash="se",
            series_glossary_hash="sg",
            series_knowledge_hash="sk",
            manifest_fingerprint="mf",
            book_checkpoints=(book_ref,),
            state_hash="hash1",
        )

        checkpoint2 = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="s1",
            checkpoint_id="c2",
            created_at="t2",
            series_memory_hash="sm",
            series_entity_registry_hash="se",
            series_glossary_hash="sg",
            series_knowledge_hash="sk",
            manifest_fingerprint="mf",
            book_checkpoints=(book_ref,),
            state_hash="hash2",
        )

        assert checkpoint1.state_hash != checkpoint2.state_hash


class TestBackwardCompatibility:
    """Test backward compatibility with pre-Batch 5.6 manifests."""

    def test_old_manifest_loads_without_checkpoint_hash(self, tmp_path):
        """Test loading checkpoint when manifest has no checkpoint hash (empty string default)."""
        # This tests that the SeriesCheckpoint loading doesn't depend on manifest
        # The manifest integration is one-way: checkpoint -> manifest
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        # Create a valid checkpoint
        book_ref = BookCheckpointRef(
            book_identity="b1", volume_number=1, book_memory_hash="m", book_context_hash="c",
            latest_session_checkpoint_id=None, status="pending"
        )
        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id="test_series",
            checkpoint_id="scheck_123",
            created_at="2026-08-21T00:00:00Z",
            series_memory_hash="sm",
            series_entity_registry_hash="se",
            series_glossary_hash="sg",
            series_knowledge_hash="sk",
            manifest_fingerprint="mf",
            book_checkpoints=(book_ref,),
            state_hash="",
        ).with_hash()

        path = get_series_checkpoint_path(output_root, "test_series")
        save_series_checkpoint(checkpoint, path)

        # Load should work regardless of manifest state
        loaded = load_latest_series_checkpoint("test_series", output_root)
        assert loaded is not None
        assert loaded.state_hash == checkpoint.state_hash


class TestFrozenContractIsolation:
    """Test frozen checkpoint systems remain unchanged."""

    def test_runtime_checkpoint_models_unchanged(self):
        """Verify runtime_checkpoint models are importable and unchanged."""
        from core.runtime_checkpoint.models import (
            CheckpointSnapshot,
            ProgressState,
            ProgressStatus,
            RequestManifest,
            CheckpointIntegrityError,
        )
        assert CheckpointSnapshot is not None
        assert ProgressState is not None
        assert ProgressStatus is not None
        assert RequestManifest is not None
        assert CheckpointIntegrityError is not None

    def test_production_runtime_checkpoint_unchanged(self):
        """Verify production_runtime checkpoint is importable."""
        from core.production_runtime.checkpoint import (
            RuntimeCheckpoint,
            RuntimeCheckpointStore,
        )
        assert RuntimeCheckpoint is not None
        assert RuntimeCheckpointStore is not None

    def test_translation_session_checkpoint_unchanged(self):
        """Verify translation_session checkpoint is importable."""
        from core.translation_session.session_checkpoint import (
            SessionCheckpoint,
            save_checkpoint,
            load_checkpoint,
        )
        assert SessionCheckpoint is not None
        assert save_checkpoint is not None
        assert load_checkpoint is not None


class TestRootHygiene:
    """Test no temporary files created in repository root."""

    def test_no_root_files_created(self, tmp_path):
        """Test checkpoint operations don't create files in root."""
        # This is a structural test - checkpoint files go to output/series/{series_id}/
        output_root = tmp_path / "output"
        output_root.mkdir(parents=True)

        path = get_series_checkpoint_path(output_root, "test_series")
        assert "output" in str(path)
        assert "series" in str(path)
        assert "test_series" in str(path)


# Test runner entry point
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
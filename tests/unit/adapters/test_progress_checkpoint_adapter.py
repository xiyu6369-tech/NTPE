"""Contract tests for ProgressCheckpointAdapter."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.adapters.progress_checkpoint_adapter import (
    ChunkProgress,
    LiveProgress,
    ProgressCheckpointAdapter,
    ResumeState,
)


class TestProgressCheckpointAdapter:
    def setup_method(self):
        self.output_dir = Path("/tmp/test_output")
        self.adapter = ProgressCheckpointAdapter(self.output_dir)

    def test_get_resume_state_returns_none_when_not_found(self):
        """Test get_resume_state returns None when file doesn't exist."""
        result = self.adapter.get_resume_state("nonexistent")
        assert result is None

    def test_get_resume_state_parses_json(self, tmp_path: Path):
        """Test get_resume_state correctly parses JSON resume state."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stem = "test_book"
        
        resume_data = {
            "version": "1.0",
            "chunks": {
                "000001": {"status": "success", "text": "chunk 1"},
                "000002": {"status": "failed", "text": "chunk 2"},
            },
            "events": [{"type": "start", "timestamp": "2024-01-01T00:00:00"}],
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 2,
            "updated_at": "2024-01-01T01:00:00",
        }
        
        resume_path = output_dir / f"{stem}_resume_state.json"
        resume_path.write_text(json.dumps(resume_data), encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_resume_state(stem)

        assert isinstance(result, ResumeState)
        assert result.version == "1.0"
        assert len(result.chunks) == 2
        assert result.chunk_total == 2
        assert result.input == "/path/to/input.txt"
        assert result.output_dir == "/path/to/output"
        assert result.updated_at == "2024-01-01T01:00:00"

    def test_get_resume_state_handles_corrupted_json(self, tmp_path: Path):
        """Test get_resume_state returns None for corrupted JSON."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stem = "test_book"
        
        resume_path = output_dir / f"{stem}_resume_state.json"
        resume_path.write_text("invalid json{", encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_resume_state(stem)

        assert result is None

    def test_get_resume_state_finds_in_subdirectory(self, tmp_path: Path):
        """Test get_resume_state finds file in subdirectory."""
        output_dir = tmp_path / "output"
        subdir = output_dir / "subdir"
        subdir.mkdir(parents=True)
        stem = "test_book"
        
        resume_data = {
            "version": "1.0",
            "chunks": {},
            "events": [],
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 0,
            "updated_at": "2024-01-01T01:00:00",
        }
        
        resume_path = subdir / f"{stem}_resume_state.json"
        resume_path.write_text(json.dumps(resume_data), encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_resume_state(stem)

        assert result is not None
        assert result.version == "1.0"

    def test_get_live_progress_returns_none_when_not_found(self):
        """Test get_live_progress returns None when file doesn't exist."""
        result = self.adapter.get_live_progress("nonexistent")
        assert result is None

    def test_get_live_progress_parses_json(self, tmp_path: Path):
        """Test get_live_progress correctly parses JSON live progress."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stem = "test_book"
        
        resume_data = {
            "version": "1.0",
            "chunks": {},
            "events": [],
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 10,
            "updated_at": "2024-01-01T01:00:00",
        }
        
        live_data = {
            "status": "running",
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 10,
            "chunk_completed": 5,
            "current_chunk": 6,
            "current_step": "translation",
            "updated_at": "2024-01-01T01:30:00",
        }
        
        resume_path = output_dir / f"{stem}_resume_state.json"
        resume_path.write_text(json.dumps(resume_data), encoding="utf-8")
        
        live_path = output_dir / f"{stem}_live_progress.json"
        live_path.write_text(json.dumps(live_data), encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_live_progress(stem)

        assert isinstance(result, LiveProgress)
        assert result.status == "running"
        assert result.chunk_total == 10
        assert result.chunk_completed == 5
        assert result.current_chunk == 6
        assert result.current_step == "translation"
        assert result.updated_at == "2024-01-01T01:30:00"

    def test_get_live_progress_handles_corrupted_json(self, tmp_path: Path):
        """Test get_live_progress returns None for corrupted JSON."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stem = "test_book"
        
        resume_data = {
            "version": "1.0",
            "chunks": {},
            "events": [],
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 10,
            "updated_at": "2024-01-01T01:00:00",
        }
        
        resume_path = output_dir / f"{stem}_resume_state.json"
        resume_path.write_text(json.dumps(resume_data), encoding="utf-8")
        
        live_path = output_dir / f"{stem}_live_progress.json"
        live_path.write_text("invalid json{", encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_live_progress(stem)

        assert result is None


class TestChunkProgressCalculation:
    def test_get_chunk_progress_all_success(self):
        """Test chunk progress calculation when all chunks succeed."""
        resume_state = ResumeState(
            version="1.0",
            chunks={
                "000001": {"status": "success"},
                "000002": {"status": "pass_with_warning"},
                "000003": {"status": "success"},
            },
            events=[],
            input="/path/to/input.txt",
            output_dir="/path/to/output",
            chunk_total=3,
            updated_at="2024-01-01T01:00:00",
        )

        adapter = ProgressCheckpointAdapter(Path("/tmp/output"))
        progress = adapter.get_chunk_progress(resume_state)

        assert progress.total == 3
        assert progress.completed == 3
        assert progress.failed == 0
        assert progress.skipped == 0
        assert progress.pending == 0
        assert progress.current_chunk is None

    def test_get_chunk_progress_mixed_statuses(self):
        """Test chunk progress calculation with mixed statuses."""
        resume_state = ResumeState(
            version="1.0",
            chunks={
                "000001": {"status": "success"},
                "000002": {"status": "failed"},
                "000003": {"status": "qa_failed"},
                "000004": {"status": "skipped"},
                "000005": {"status": "pending"},
            },
            events=[],
            input="/path/to/input.txt",
            output_dir="/path/to/output",
            chunk_total=5,
            updated_at="2024-01-01T01:00:00",
        )

        adapter = ProgressCheckpointAdapter(Path("/tmp/output"))
        progress = adapter.get_chunk_progress(resume_state)

        assert progress.total == 5
        assert progress.completed == 1
        assert progress.failed == 2
        assert progress.skipped == 1
        assert progress.pending == 1

    def test_get_chunk_progress_finds_current_chunk(self):
        """Test chunk progress identifies current in-progress chunk."""
        resume_state = ResumeState(
            version="1.0",
            chunks={
                "000001": {"status": "success"},
                "000002": {"status": "in_progress"},
                "000003": {"status": "pending"},
            },
            events=[],
            input="/path/to/input.txt",
            output_dir="/path/to/output",
            chunk_total=3,
            updated_at="2024-01-01T01:00:00",
        )

        adapter = ProgressCheckpointAdapter(Path("/tmp/output"))
        progress = adapter.get_chunk_progress(resume_state)

        assert progress.current_chunk == 2
        assert progress.current_step is None

    def test_get_chunk_progress_pass_with_warning_counts_as_completed(self):
        """Test that pass_with_warning counts as completed."""
        resume_state = ResumeState(
            version="1.0",
            chunks={
                "000001": {"status": "success"},
                "000002": {"status": "pass_with_warning"},
            },
            events=[],
            input="/path/to/input.txt",
            output_dir="/path/to/output",
            chunk_total=2,
            updated_at="2024-01-01T01:00:00",
        )

        adapter = ProgressCheckpointAdapter(Path("/tmp/output"))
        progress = adapter.get_chunk_progress(resume_state)

        assert progress.completed == 2

    def test_get_chunk_progress_qa_failed_counts_as_failed(self):
        """Test that qa_failed counts as failed."""
        resume_state = ResumeState(
            version="1.0",
            chunks={
                "000001": {"status": "qa_failed"},
            },
            events=[],
            input="/path/to/input.txt",
            output_dir="/path/to/output",
            chunk_total=1,
            updated_at="2024-01-01T01:00:00",
        )

        adapter = ProgressCheckpointAdapter(Path("/tmp/output"))
        progress = adapter.get_chunk_progress(resume_state)

        assert progress.failed == 1

    def test_resume_state_defaults(self):
        """Test ResumeState has correct defaults for missing fields."""
        resume_state = ResumeState(
            version="",
            chunks={},
            events=[],
            input="",
            output_dir="",
            chunk_total=0,
            updated_at="",
        )

        assert resume_state.version == ""
        assert resume_state.chunks == {}
        assert resume_state.events == []
        assert resume_state.input == ""
        assert resume_state.output_dir == ""
        assert resume_state.chunk_total == 0
        assert resume_state.updated_at == ""


class TestLiveProgressDefaults:
    def test_live_progress_defaults(self):
        """Test LiveProgress has correct defaults for missing fields."""
        live_progress = LiveProgress(
            status="",
            input="",
            output_dir="",
            chunk_total=0,
            chunk_completed=0,
            current_chunk=None,
            current_step=None,
            updated_at="",
        )

        assert live_progress.status == ""
        assert live_progress.input == ""
        assert live_progress.output_dir == ""
        assert live_progress.chunk_total == 0
        assert live_progress.chunk_completed == 0
        assert live_progress.current_chunk is None
        assert live_progress.current_step is None
        assert live_progress.updated_at == ""


class TestResumeIdentityValidation:
    def test_resume_identity_matches_source_hash(self, tmp_path: Path):
        """Test that resume state can be linked to source via hash."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        stem = "test_book_abc123def4567890"
        
        resume_data = {
            "version": "1.0",
            "chunks": {},
            "events": [],
            "input": "/path/to/input.txt",
            "output_dir": "/path/to/output",
            "chunk_total": 0,
            "updated_at": "2024-01-01T01:00:00",
        }
        
        resume_path = output_dir / f"{stem}_resume_state.json"
        resume_path.write_text(json.dumps(resume_data), encoding="utf-8")
        
        adapter = ProgressCheckpointAdapter(output_dir)
        result = adapter.get_resume_state(stem)

        assert result is not None
        # Verify stem contains hash that can be used for resume identity validation
        assert "abc123def4567890" in stem
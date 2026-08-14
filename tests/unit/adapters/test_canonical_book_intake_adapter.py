"""Contract tests for CanonicalBookIntakeAdapter."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.adapters.canonical_book_intake_adapter import (
    CanonicalBookIntakeAdapter,
    CanonicalIntakeRequest,
    CanonicalIntakeResult,
    SourceIdentity,
)


class TestCanonicalBookIntakeAdapter:
    def test_process_ready_status(self, tmp_path: Path):
        """Test processing a source with ready status."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content for intake")

        adapter = CanonicalBookIntakeAdapter()
        
        # Create mock intake result
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "en"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            # Compute source identity
            content = source.read_bytes()
            source_hash = hashlib.sha256(content).hexdigest()[:16]
            stat = source.stat()
            source_identity = SourceIdentity(
                source_path=source,
                source_hash=source_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            request = CanonicalIntakeRequest(
                source_path=source,
                source_identity=source_identity,
            )
            result = adapter.process(request)

        assert isinstance(result, CanonicalIntakeResult)
        assert result.status == "ready"
        assert result.submission_eligible is True
        assert result.source_identity == source_identity
        assert result.warnings == ()

    def test_process_ready_with_warnings_status(self, tmp_path: Path):
        """Test processing a source with ready_with_warnings status."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready_with_warnings"
        mock_intake_result.quality_report.status = "warning"
        mock_intake_result.language_result.language = "en"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            content = source.read_bytes()
            source_hash = hashlib.sha256(content).hexdigest()[:16]
            stat = source.stat()
            source_identity = SourceIdentity(
                source_path=source,
                source_hash=source_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            request = CanonicalIntakeRequest(
                source_path=source,
                source_identity=source_identity,
            )
            result = adapter.process(request)

        assert result.status == "ready_with_warnings"
        assert result.submission_eligible is True
        assert "Text quality warnings detected during intake" in result.warnings

    def test_process_rejected_status(self, tmp_path: Path):
        """Test processing a source that gets rejected."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "rejected"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "en"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            content = source.read_bytes()
            source_hash = hashlib.sha256(content).hexdigest()[:16]
            stat = source.stat()
            source_identity = SourceIdentity(
                source_path=source,
                source_hash=source_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            request = CanonicalIntakeRequest(
                source_path=source,
                source_identity=source_identity,
            )
            result = adapter.process(request)

        assert result.status == "rejected"
        assert result.submission_eligible is False

    def test_process_unknown_language_warning(self, tmp_path: Path):
        """Test warning when language detection is uncertain."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "unknown"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            content = source.read_bytes()
            source_hash = hashlib.sha256(content).hexdigest()[:16]
            stat = source.stat()
            source_identity = SourceIdentity(
                source_path=source,
                source_hash=source_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            request = CanonicalIntakeRequest(
                source_path=source,
                source_identity=source_identity,
            )
            result = adapter.process(request)

        assert "Language detection uncertain: unknown" in result.warnings

    def test_process_mixed_language_warning(self, tmp_path: Path):
        """Test warning when language detection is mixed."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "mixed"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            content = source.read_bytes()
            source_hash = hashlib.sha256(content).hexdigest()[:16]
            stat = source.stat()
            source_identity = SourceIdentity(
                source_path=source,
                source_hash=source_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            request = CanonicalIntakeRequest(
                source_path=source,
                source_identity=source_identity,
            )
            result = adapter.process(request)

        assert "Language detection uncertain: mixed" in result.warnings

    def test_process_path_computes_identity(self, tmp_path: Path):
        """Test process_path computes source identity correctly."""
        source = tmp_path / "test.txt"
        source.write_text("Test content for path processing")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "en"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result):
            result = adapter.process_path(source)

        assert result.source_identity.source_path == source
        assert len(result.source_identity.source_hash) == 16
        assert result.source_identity.file_size > 0
        assert result.source_identity.modified_time > 0

    def test_process_path_calls_processor_with_correct_path(self, tmp_path: Path):
        """Test that process_path calls processor with the correct source path."""
        source = tmp_path / "test.txt"
        source.write_text("Test content")

        adapter = CanonicalBookIntakeAdapter()
        
        mock_intake_result = MagicMock()
        mock_intake_result.status = "ready"
        mock_intake_result.quality_report.status = "pass"
        mock_intake_result.language_result.language = "en"

        with patch.object(adapter.processor, "process", return_value=mock_intake_result) as mock_process:
            adapter.process_path(source)

        mock_process.assert_called_once_with(source)

    def test_source_identity_fields(self, tmp_path: Path):
        """Test SourceIdentity dataclass has all required fields."""
        source = tmp_path / "test.txt"
        source.write_text("Content")
        
        content = source.read_bytes()
        source_hash = hashlib.sha256(content).hexdigest()[:16]
        stat = source.stat()
        
        identity = SourceIdentity(
            source_path=source,
            source_hash=source_hash,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )

        assert identity.source_path == source
        assert identity.source_hash == source_hash
        assert identity.file_size == stat.st_size
        assert identity.modified_time == stat.st_mtime

    def test_canonical_intake_result_fields(self, tmp_path: Path):
        """Test CanonicalIntakeResult dataclass has all required fields."""
        mock_intake_result = MagicMock()
        source_identity = SourceIdentity(
            source_path=tmp_path / "test.txt",
            source_hash="abc123",
            file_size=100,
            modified_time=1234567890.0,
        )
        
        result = CanonicalIntakeResult(
            intake_result=mock_intake_result,
            source_identity=source_identity,
            status="ready",
            warnings=("warning1", "warning2"),
            submission_eligible=True,
        )

        assert result.intake_result == mock_intake_result
        assert result.source_identity == source_identity
        assert result.status == "ready"
        assert result.warnings == ("warning1", "warning2")
        assert result.submission_eligible is True

    def test_manual_review_enforcement_via_status(self, tmp_path: Path):
        """Test that manual review status makes submission ineligible."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        # Test statuses that should NOT be submission eligible
        non_eligible_statuses = ["rejected", "manual_review", "pending", "error"]
        
        for status in non_eligible_statuses:
            mock_intake_result = MagicMock()
            mock_intake_result.status = status
            mock_intake_result.quality_report.status = "pass"
            mock_intake_result.language_result.language = "en"

            with patch.object(adapter.processor, "process", return_value=mock_intake_result):
                content = source.read_bytes()
                source_hash = hashlib.sha256(content).hexdigest()[:16]
                stat = source.stat()
                source_identity = SourceIdentity(
                    source_path=source,
                    source_hash=source_hash,
                    file_size=stat.st_size,
                    modified_time=stat.st_mtime,
                )

                request = CanonicalIntakeRequest(
                    source_path=source,
                    source_identity=source_identity,
                )
                result = adapter.process(request)

            assert result.submission_eligible is False, f"Status '{status}' should not be submission eligible"

    def test_submission_eligible_statuses(self, tmp_path: Path):
        """Test that ready and ready_with_warnings are submission eligible."""
        source = tmp_path / "test.txt"
        source.write_text("Sample content")

        adapter = CanonicalBookIntakeAdapter()
        
        eligible_statuses = ["ready", "ready_with_warnings"]
        
        for status in eligible_statuses:
            mock_intake_result = MagicMock()
            mock_intake_result.status = status
            mock_intake_result.quality_report.status = "pass"
            mock_intake_result.language_result.language = "en"

            with patch.object(adapter.processor, "process", return_value=mock_intake_result):
                content = source.read_bytes()
                source_hash = hashlib.sha256(content).hexdigest()[:16]
                stat = source.stat()
                source_identity = SourceIdentity(
                    source_path=source,
                    source_hash=source_hash,
                    file_size=stat.st_size,
                    modified_time=stat.st_mtime,
                )

                request = CanonicalIntakeRequest(
                    source_path=source,
                    source_identity=source_identity,
                )
                result = adapter.process(request)

            assert result.submission_eligible is True, f"Status '{status}' should be submission eligible"
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
from core.adapters.epub_extraction_boundary import (
    ChapterBoundary,
    EpubExtractionError,
    ExtractionManifest,
    ExtractedTextIntakeRequest,
    ResourceRef,
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

    # ============================================================
    # ingest_extracted tests (EPUB Canonical Intake Integration)
    # ============================================================

    def _make_extracted_request(self, tmp_path: Path, status: str = "success", warnings: tuple[str, ...] = ()) -> ExtractedTextIntakeRequest:
        """Create a minimal ExtractedTextIntakeRequest for testing."""
        source = tmp_path / "test.epub"
        source.write_bytes(b"dummy")
        extracted_text = "안녕하세요 반갑습니다 이것은 한국어 텍스트입니다."
        original_hash = hashlib.sha256(b"dummy").hexdigest()
        extracted_hash = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()

        manifest = ExtractionManifest(
            extractor_version="epub-extraction-v1.0.0",
            extracted_at="2024-01-01T00:00:00Z",
            chapter_count=1,
            total_characters=len(extracted_text),
            total_words=len(extracted_text.split()),
            warnings=warnings,
            resources=(),
            spine_item_count=1,
            nav_toc_entries=1,
            encoding_used="utf-8",
            parsing_duration_ms=100,
        )

        chapter_map = (
            ChapterBoundary(
                index=1,
                spine_position=1,
                title="Chapter 1",
                start_offset=0,
                end_offset=len(extracted_text),
                source_href="chapter1.xhtml",
                toc_level=1,
                is_linear=True,
                word_count=len(extracted_text.split()),
                landmark_type="bodymatter",
                status="linear",
            ),
)

        return ExtractedTextIntakeRequest(
            source_path=source,
            source_format="epub",
            extracted_text=extracted_text,
            original_file_hash=original_hash,
            extracted_text_hash=extracted_hash,
            epub_metadata={
                "title": "Test Book",
                "author": "Test Author",
                "language": "ko",
                "identifier": "test-id",
                "publisher": "Test Publisher",
                "date": "2024-01-01",
                "raw": {},
            },
            chapter_map=chapter_map,
            extraction_manifest=manifest,
            extractor_version="epub-extraction-v1.0.0",
            status=status,
            warnings=warnings,
        )

    def test_ingest_extracted_valid_epub_succeeds(self, tmp_path: Path):
        """Test valid EPUB extraction flows through canonical intake successfully."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path, status="success")

        result = adapter.ingest_extracted(request)

        assert isinstance(result, CanonicalIntakeResult)
        assert result.status in ("ready", "ready_with_warnings")
        assert result.submission_eligible is True
        assert result.source_identity.source_hash == request.original_file_hash[:16]
        assert result.epub_metadata is not None
        assert result.epub_metadata["title"] == "Test Book"
        assert result.epub_metadata["author"] == "Test Author"
        assert result.chapter_map is not None
        assert len(result.chapter_map) == 1
        assert result.chapter_map[0].title == "Chapter 1"
        assert result.resource_refs is not None
        assert result.extraction_manifest is not None
        assert result.extraction_provenance is not None
        assert result.extraction_provenance["extractor_version"] == "epub-extraction-v1.0.0"

    def test_ingest_extracted_blocked_status_raises(self, tmp_path: Path):
        """Test that blocked extraction status raises EpubExtractionError (fail closed)."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path, status="blocked", warnings=("zip bomb detected",))

        with pytest.raises(EpubExtractionError) as exc_info:
            adapter.ingest_extracted(request)

        assert exc_info.value.blocked is True
        assert "zip bomb" in str(exc_info.value).lower()

    def test_ingest_extracted_manual_review_status_raises(self, tmp_path: Path):
        """Test that manual_review_required status raises EpubExtractionError (fail closed)."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path, status="manual_review_required", warnings=("remote image resource detected",))

        with pytest.raises(EpubExtractionError) as exc_info:
            adapter.ingest_extracted(request)

        assert exc_info.value.blocked is False
        assert "remote image" in str(exc_info.value).lower()

    def test_ingest_extracted_partial_status_proceeds_with_warnings(self, tmp_path: Path):
        """Test that partial extraction status proceeds but includes warnings."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path, status="partial", warnings=("parse error in chapter 2",))

        result = adapter.ingest_extracted(request)

        assert result.status in ("ready", "ready_with_warnings", "manual_review_required")
        assert "parse error" in str(result.warnings).lower()

    def test_ingest_extracted_metadata_preservation(self, tmp_path: Path):
        """Test that EPUB metadata is preserved in canonical intake result."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.epub_metadata is not None
        assert result.epub_metadata["title"] == "Test Book"
        assert result.epub_metadata["author"] == "Test Author"
        assert result.epub_metadata["language"] == "ko"
        assert result.epub_metadata["identifier"] == "test-id"
        assert result.epub_metadata["publisher"] == "Test Publisher"
        assert result.epub_metadata["date"] == "2024-01-01"

    def test_ingest_extracted_chapter_map_preservation(self, tmp_path: Path):
        """Test that chapter map is preserved with all boundary information."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.chapter_map is not None
        assert len(result.chapter_map) == 1
        chapter = result.chapter_map[0]
        assert chapter.index == 1
        assert chapter.spine_position == 1
        assert chapter.title == "Chapter 1"
        assert chapter.start_offset == 0
        assert chapter.end_offset > 0
        assert chapter.source_href == "chapter1.xhtml"
        assert chapter.toc_level == 1
        assert chapter.is_linear is True
        assert chapter.word_count > 0
        assert chapter.landmark_type == "bodymatter"
        assert chapter.status == "linear"

    def test_ingest_extracted_resource_tracking_preservation(self, tmp_path: Path):
        """Test that resource references are preserved."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.resource_refs is not None
        assert isinstance(result.resource_refs, tuple)

    def test_ingest_extracted_source_identity_deterministic(self, tmp_path: Path):
        """Test that source identity is deterministic based on original_file_hash."""
        adapter = CanonicalBookIntakeAdapter()
        request1 = self._make_extracted_request(tmp_path)
        request2 = self._make_extracted_request(tmp_path)

        result1 = adapter.ingest_extracted(request1)
        result2 = adapter.ingest_extracted(request2)

        assert result1.source_identity.source_hash == result2.source_identity.source_hash
        assert result1.source_identity.source_hash == request1.original_file_hash[:16]

    def test_ingest_extracted_extraction_provenance(self, tmp_path: Path):
        """Test that extraction provenance is recorded."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.extraction_provenance is not None
        assert result.extraction_provenance["extractor_version"] == "epub-extraction-v1.0.0"
        assert result.extraction_provenance["extracted_text_hash"] == request.extracted_text_hash
        assert result.extraction_provenance["extraction_status"] == "success"
        assert result.extraction_provenance["original_file_hash"] == request.original_file_hash

    def test_ingest_extracted_preserves_warnings(self, tmp_path: Path):
        """Test that extraction warnings are preserved in result."""
        adapter = CanonicalBookIntakeAdapter()
        warnings = ("warning 1", "warning 2")
        request = self._make_extracted_request(tmp_path, status="success", warnings=warnings)

        result = adapter.ingest_extracted(request)

        for w in warnings:
            assert w in result.warnings

    def test_ingest_extracted_language_detection_korean(self, tmp_path: Path):
        """Test that Korean text is detected correctly through BookIntakeProcessor."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.intake_result.language_result.language == "ko"
        assert result.intake_result.language_result.confidence > 0

    def test_ingest_extracted_quality_analysis(self, tmp_path: Path):
        """Test that text quality analysis runs on extracted text."""
        adapter = CanonicalBookIntakeAdapter()
        request = self._make_extracted_request(tmp_path)

        result = adapter.ingest_extracted(request)

        assert result.intake_result.quality_report is not None
        assert result.intake_result.quality_report.status in ("clean", "warning", "manual_review_required", "blocked")
        assert result.intake_result.quality_report.score >= 0
        assert isinstance(result.intake_result.quality_report.findings, tuple)

    def test_ingest_extracted_txt_regression_unchanged(self, tmp_path: Path):
        """Test that TXT path (process/process_path) remains unchanged."""
        source = tmp_path / "test.txt"
        source.write_text("Sample English text for testing.")

        adapter = CanonicalBookIntakeAdapter()

        result1 = adapter.process_path(source)
        result2 = adapter.process_path(source)

        assert result1.status == result2.status
        assert result1.source_identity.source_hash == result2.source_identity.source_hash
        assert result1.intake_result.text == result2.intake_result.text
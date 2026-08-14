"""Contract tests for EpubExtractionBoundary."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.adapters.epub_extraction_boundary import (
    ChapterBoundary,
    EpubExtractionBoundary,
    EpubExtractionResult,
    EpubMetadata,
    ExtractionManifest,
)


class TestEpubExtractionBoundary:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_extract_raises_not_implemented_error(self, tmp_path: Path):
        """Test that extract raises NotImplementedError."""
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(b"fake epub content")

        with pytest.raises(NotImplementedError) as exc_info:
            self.boundary.extract(epub_path)

        assert "EPUB extraction is not implemented in P0 Stage 1" in str(exc_info.value)
        assert "architecture definition only" in str(exc_info.value)

    def test_validate_epub_returns_false_for_nonexistent_file(self, tmp_path: Path):
        """Test validate_epub returns False for non-existent file."""
        epub_path = tmp_path / "nonexistent.epub"

        is_valid, error = self.boundary.validate_epub(epub_path)

        assert is_valid is False
        assert error is not None
        assert "not found" in error.lower()

    def test_validate_epub_returns_false_for_wrong_extension(self, tmp_path: Path):
        """Test validate_epub returns False for non-EPUB file."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not an epub")

        is_valid, error = self.boundary.validate_epub(txt_path)

        assert is_valid is False
        assert error is not None
        assert "not an epub" in error.lower()

    def test_validate_epub_returns_true_when_ebooklib_available(self, tmp_path: Path):
        """Test validate_epub returns True when ebooklib is available."""
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(b"fake epub content")

        # Need to patch the import inside the method
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "ebooklib":
                return MagicMock()
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            is_valid, error = self.boundary.validate_epub(epub_path)

        assert is_valid is True
        assert error is None

    def test_validate_epub_returns_false_when_ebooklib_not_installed(self, tmp_path: Path):
        """Test validate_epub returns False when ebooklib is not installed."""
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(b"fake epub content")

        with patch("builtins.__import__", side_effect=ImportError("No module named 'ebooklib'")):
            is_valid, error = self.boundary.validate_epub(epub_path)

        assert is_valid is False
        assert error is not None
        assert "ebooklib not installed" in error

    def test_extractor_version(self):
        """Test extractor_version is set."""
        assert self.boundary.extractor_version == "epub-extraction-boundary-v0.1"


class TestEpubExtractionDataStructures:
    def test_epub_metadata_fields(self):
        """Test EpubMetadata dataclass has all required fields."""
        metadata = EpubMetadata(
            title="Test Book",
            author="Test Author",
            language="en",
            identifier="isbn123",
            publisher="Test Publisher",
            date="2024-01-01",
            raw={"meta": "data"},
        )

        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
        assert metadata.language == "en"
        assert metadata.identifier == "isbn123"
        assert metadata.publisher == "Test Publisher"
        assert metadata.date == "2024-01-01"
        assert metadata.raw == {"meta": "data"}

    def test_epub_metadata_optional_fields(self):
        """Test EpubMetadata allows None for optional fields."""
        metadata = EpubMetadata(
            title=None,
            author=None,
            language=None,
            identifier=None,
            publisher=None,
            date=None,
            raw={},
        )

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.identifier is None
        assert metadata.publisher is None
        assert metadata.date is None
        assert metadata.raw == {}

    def test_chapter_boundary_fields(self):
        """Test ChapterBoundary dataclass has all required fields."""
        chapter = ChapterBoundary(
            index=1,
            title="Chapter 1",
            start_offset=0,
            end_offset=1000,
            source_href="chapter1.xhtml",
        )

        assert chapter.index == 1
        assert chapter.title == "Chapter 1"
        assert chapter.start_offset == 0
        assert chapter.end_offset == 1000
        assert chapter.source_href == "chapter1.xhtml"

    def test_chapter_boundary_optional_fields(self):
        """Test ChapterBoundary allows None for optional fields."""
        chapter = ChapterBoundary(
            index=1,
            title=None,
            start_offset=0,
            end_offset=1000,
            source_href=None,
        )

        assert chapter.index == 1
        assert chapter.title is None
        assert chapter.start_offset == 0
        assert chapter.end_offset == 1000
        assert chapter.source_href is None

    def test_extraction_manifest_fields(self):
        """Test ExtractionManifest dataclass has all required fields."""
        manifest = ExtractionManifest(
            extractor_version="v1.0",
            extracted_at="2024-01-01T00:00:00",
            chapter_count=5,
            total_characters=50000,
            warnings=("warning1", "warning2"),
        )

        assert manifest.extractor_version == "v1.0"
        assert manifest.extracted_at == "2024-01-01T00:00:00"
        assert manifest.chapter_count == 5
        assert manifest.total_characters == 50000
        assert manifest.warnings == ("warning1", "warning2")

    def test_epub_extraction_result_fields(self, tmp_path: Path):
        """Test EpubExtractionResult dataclass has all required fields."""
        epub_path = tmp_path / "test.epub"
        metadata = EpubMetadata(
            title="Test",
            author="Author",
            language="en",
            identifier="id123",
            publisher="Pub",
            date="2024",
            raw={},
        )
        chapters = (
            ChapterBoundary(1, "Ch1", 0, 100, "ch1.xhtml"),
            ChapterBoundary(2, "Ch2", 100, 200, "ch2.xhtml"),
        )
        manifest = ExtractionManifest("v1", "2024", 2, 200, ())

        result = EpubExtractionResult(
            source_path=epub_path,
            original_hash="abc123",
            extracted_text="Full text",
            extracted_hash="def456",
            metadata=metadata,
            chapter_map=chapters,
            extraction_manifest=manifest,
            status="success",
            warnings=(),
        )

        assert result.source_path == epub_path
        assert result.original_hash == "abc123"
        assert result.extracted_text == "Full text"
        assert result.extracted_hash == "def456"
        assert result.metadata == metadata
        assert result.chapter_map == chapters
        assert result.extraction_manifest == manifest
        assert result.status == "success"
        assert result.warnings == ()

    def test_stub_behavior_contract(self, tmp_path: Path):
        """Test that the stub behavior is consistent and documented."""
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(b"content")

        boundary = EpubExtractionBoundary()

        # The extract method should always raise NotImplementedError
        with pytest.raises(NotImplementedError):
            boundary.extract(epub_path)

        # The error message should contain specific guidance
        try:
            boundary.extract(epub_path)
        except NotImplementedError as e:
            error_msg = str(e)
            assert "P0 Stage 1" in error_msg
            assert "architecture definition" in error_msg
            assert "subsequent stage" in error_msg

    def test_validate_epub_contract(self, tmp_path: Path):
        """Test validate_epub contract: returns (bool, str|None)."""
        boundary = EpubExtractionBoundary()

        # Test with non-existent file
        result = boundary.validate_epub(tmp_path / "missing.epub")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

        # Test with wrong extension
        txt = tmp_path / "test.txt"
        txt.write_text("text")
        result = boundary.validate_epub(txt)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)
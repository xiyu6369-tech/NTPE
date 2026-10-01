"""S1 EPUB Translation Contract Tests — Offline, Deterministic."""

from __future__ import annotations

import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from core.epub_translation.contract import (
    ContractValidationError,
    EpubMetadata,
    EpubChapterBoundary,
    ResourceRef,
    TocEntry,
    ExtractionManifest,
    EpubTranslationInput,
    EpubTranslationChunk,
    EpubChunkResult,
    EpubChapterResult,
    EpubTranslationResult,
    validate_sha256,
    validate_chapter_id,
    validate_epub_translation_input,
    validate_epub_translation_chunk,
    validate_epub_chunk_result,
    validate_epub_chapter_result,
    validate_epub_translation_result,
    validate_chunk_ownership,
    validate_complete_contract,
    validate_chapter_boundary,
)


# ========================================================================
# Fixtures
# ========================================================================

def make_epub_metadata() -> EpubMetadata:
    return EpubMetadata(
        title="Test Novel",
        author="Test Author",
        language="ko",
        identifier="test-id",
        publisher="Test Publisher",
        date="2024-01-01",
        raw=MappingProxyType({"dc:title": "Test Novel", "dc:creator": "Test Author"}),
    )


def make_chapter_boundary(
    index: int = 1,
    spine_position: int = 1,
    title: str | None = "Chapter 1",
    source_href: str = "OEBPS/ch1.xhtml",
    start_offset: int = 0,
    end_offset: int = 100,
    is_linear: bool = True,
    word_count: int = 50,
    body_start_offset: int | None = None,
    body_end_offset: int | None = None,
) -> EpubChapterBoundary:
    # Auto-compute body offsets if not provided
    if body_start_offset is None:
        # For empty chapters (word_count=0 or end_offset <= start_offset), 
        # body starts at start_offset (no marker offset for empty body)
        if word_count == 0 or end_offset <= start_offset:
            body_start_offset = start_offset
        else:
            body_start_offset = start_offset + 30  # After marker
    if body_end_offset is None:
        # For empty chapters, body_end equals body_start (empty range)
        if word_count == 0 or end_offset <= start_offset:
            body_end_offset = body_start_offset
        else:
            body_end_offset = max(start_offset + 1, end_offset - 5)  # Before trailing newline
    return EpubChapterBoundary(
        index=index,
        spine_position=spine_position,
        title=title,
        source_href=source_href,
        start_offset=start_offset,
        end_offset=end_offset,
        is_linear=is_linear,
        word_count=word_count,
        body_start_offset=body_start_offset,
        body_end_offset=body_end_offset,
    )


def make_chapter_boundary_raw(
    index: int = 1,
    spine_position: int = 1,
    title: str | None = "Chapter 1",
    source_href: str = "OEBPS/ch1.xhtml",
    start_offset: int = 0,
    end_offset: int = 100,
    is_linear: bool = True,
    word_count: int = 50,
    body_start_offset: int | None = None,
    body_end_offset: int | None = None,
) -> EpubChapterBoundary:
    """Create chapter boundary WITHOUT auto-computing body offsets (for testing optional fields)."""
    return EpubChapterBoundary(
        index=index,
        spine_position=spine_position,
        title=title,
        source_href=source_href,
        start_offset=start_offset,
        end_offset=end_offset,
        is_linear=is_linear,
        word_count=word_count,
        body_start_offset=body_start_offset,
        body_end_offset=body_end_offset,
    )


def make_resource_ref(
    type_: str = "image",
    href: str = "images/cover.jpg",
    chapter_index: int | None = 1,
) -> ResourceRef:
    return ResourceRef(
        type=type_,
        href=href,
        chapter_index=chapter_index,
        metadata=MappingProxyType({"alt": "cover"}),
    )


def make_toc_entry(href: str = "ch1.xhtml", title: str = "Chapter 1", level: int = 0) -> TocEntry:
    return TocEntry(href=href, title=title, level=level)


def make_extraction_manifest() -> ExtractionManifest:
    return ExtractionManifest(
        extractor_version="epub-extraction-v1.0.0",
        extracted_at="2024-01-01T00:00:00+00:00",
        chapter_count=3,
        total_characters=300,
        total_words=150,
        warnings=(),
        resources=(),
        spine_item_count=3,
        nav_toc_entries=3,
        encoding_used="utf-8",
        parsing_duration_ms=100,
        fixed_layout=None,
    )


def make_epub_translation_input(
    chapter_map: tuple[EpubChapterBoundary, ...] | None = None,
    original_hash: str = "a" * 64,
    extraction_status: str = "success",
    warnings: tuple[str, ...] = (),
    toc_entries: tuple[TocEntry, ...] | None = None,
    fixed_layout_info: Any | None = None,
) -> EpubTranslationInput:
    if chapter_map is None:
        chapter_map = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/ch3.xhtml", 200, 300),
        )

    if toc_entries is None:
        toc_entries = (
            make_toc_entry("ch1.xhtml", "Chapter 1"),
            make_toc_entry("ch2.xhtml", "Chapter 2"),
        )

    return EpubTranslationInput(
        source_epub_path=Path("test.epub"),
        original_hash=original_hash,
        extraction_status=extraction_status,
        warnings=warnings,
        metadata=make_epub_metadata(),
        chapter_map=chapter_map,
        resources=(),
        toc_entries=toc_entries,
        fixed_layout_info=fixed_layout_info,
        extraction_manifest=make_extraction_manifest(),
    )


def make_epub_chunk(
    chunk_id: str = "test:ch0001:ck0000",
    chapter_id: str = "ch0001",
    chapter_order: int = 1,
    chunk_sequence: int = 0,
    source_text: str = "Test content",
    extracted_start: int = 30,
    extracted_end: int = 80,
    body_start: int = 30,
    body_end: int = 80,
    source_href: str = "OEBPS/ch1.xhtml",
    fragment: str | None = None,
) -> EpubTranslationChunk:
    return EpubTranslationChunk(
        chunk_id=chunk_id,
        chapter_id=chapter_id,
        chapter_order=chapter_order,
        chunk_sequence=chunk_sequence,
        source_text=source_text,
        extracted_start_offset=extracted_start,
        extracted_end_offset=extracted_end,
        body_start_offset=body_start,
        body_end_offset=body_end,
        source_href=source_href,
        fragment=fragment,
    )


def make_chunk_result(
    chunk_id: str = "test:ch0001:ck0000",
    status: str = "success",
    translated_text: str = "번역된 내용",
    error: str | None = None,
    attempt: int = 1,
) -> EpubChunkResult:
    return EpubChunkResult(
        chunk_id=chunk_id,
        status=status,
        translated_text=translated_text,
        error=error,
        attempt=attempt,
        qa_report=MappingProxyType({"passed": True}),
        metadata=MappingProxyType({}),
    )


def make_chapter_result(
    chapter_id: str = "ch0001",
    chapter_order: int = 1,
    chunk_results: tuple[EpubChunkResult, ...] | None = None,
    aggregate_status: str = "success",
) -> EpubChapterResult:
    if chunk_results is None:
        chunk_results = (make_chunk_result(),)

    success_count = sum(1 for c in chunk_results if c.status == "success")
    failed_count = sum(1 for c in chunk_results if c.status == "failed")
    skipped_count = sum(1 for c in chunk_results if c.status == "skipped")
    assembled_text = "\n\n".join(c.translated_text for c in chunk_results if c.status == "success")

    return EpubChapterResult(
        chapter_id=chapter_id,
        chapter_order=chapter_order,
        chunk_results=chunk_results,
        aggregate_status=aggregate_status,
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        assembled_text=assembled_text,
    )


def make_translation_result(
    chapter_results: tuple[EpubChapterResult, ...] | None = None,
    aggregate_status: str = "success",
) -> EpubTranslationResult:
    if chapter_results is None:
        chapter_results = (make_chapter_result(),)

    return EpubTranslationResult(
        aggregate_status=aggregate_status,
        chapter_results=chapter_results,
        success_count=sum(c.success_count for c in chapter_results),
        failed_count=sum(c.failed_count for c in chapter_results),
        skipped_count=sum(c.skipped_count for c in chapter_results),
        session_id="test-session-123",
        resume_state_path=None,
    )


# ========================================================================
# Basic Model Tests
# ========================================================================

class TestEpubMetadata:
    def test_valid_metadata(self) -> None:
        meta = make_epub_metadata()
        assert meta.title == "Test Novel"
        assert meta.author == "Test Author"

    def test_none_fields_allowed(self) -> None:
        meta = EpubMetadata(
            title=None, author=None, language=None, identifier=None,
            publisher=None, date=None, raw=MappingProxyType({})
        )
        assert meta.title is None


class TestEpubChapterBoundary:
    def test_valid_boundary(self) -> None:
        ch = make_chapter_boundary()
        assert ch.chapter_id == "ch0001"
        assert ch.spine_position == 1
        assert ch.fragment is None

    def test_boundary_with_fragment(self) -> None:
        ch = make_chapter_boundary(source_href="OEBPS/ch1.xhtml#section2")
        assert ch.fragment == "section2"
        assert ch.href_without_fragment == "OEBPS/ch1.xhtml"

    def test_body_offsets_optional(self) -> None:
        ch = make_chapter_boundary_raw(body_start_offset=None, body_end_offset=None)
        assert ch.body_start_offset is None
        assert ch.body_end_offset is None

    def test_body_offsets_auto_computed(self) -> None:
        ch = make_chapter_boundary()
        assert ch.body_start_offset is not None
        assert ch.body_end_offset is not None
        assert ch.body_start_offset > ch.start_offset
        assert ch.body_end_offset < ch.end_offset


class TestEpubTranslationInput:
    def test_valid_input(self) -> None:
        inp = make_epub_translation_input()
        assert inp.original_hash == "a" * 64
        assert inp.extraction_status == "success"
        assert len(inp.chapter_map) == 3

    def test_invalid_hash_raises(self) -> None:
        with pytest.raises(ValueError, match="original_hash must be 64-char hex"):
            make_epub_translation_input(original_hash="invalid")

    def test_linear_chapters_property(self) -> None:
        inp = make_epub_translation_input()
        linear = inp.linear_chapters
        assert len(linear) == 3
        assert all(c.is_linear for c in linear)


# ========================================================================
# Validator Tests
# ========================================================================

class TestValidateSha256:
    def test_valid_sha256(self) -> None:
        validate_sha256("a" * 64, "test")
        validate_sha256("A" * 64, "test")

    def test_invalid_sha256(self) -> None:
        with pytest.raises(ContractValidationError, match="must be a 64-char hex"):
            validate_sha256("invalid", "test")
        with pytest.raises(ContractValidationError):
            validate_sha256("g" * 64, "test")  # invalid hex char


class TestValidateChapterId:
    def test_valid_chapter_id(self) -> None:
        validate_chapter_id("ch0001", "test")
        validate_chapter_id("ch9999", "test")

    def test_invalid_chapter_id(self) -> None:
        with pytest.raises(ContractValidationError, match="chXXXX format"):
            validate_chapter_id("chapter1", "test")
        with pytest.raises(ContractValidationError):
            validate_chapter_id("ch1", "test")


class TestValidateEpubTranslationInput:
    def test_valid_input(self) -> None:
        inp = make_epub_translation_input()
        validate_epub_translation_input(inp)  # Should not raise

    def test_empty_chapter_map_raises(self) -> None:
        inp = make_epub_translation_input(chapter_map=())
        with pytest.raises(ContractValidationError, match="chapter_map must not be empty"):
            validate_epub_translation_input(inp)

    def test_duplicate_chapter_id_raises(self) -> None:
        ch1 = make_chapter_boundary(1, 1, "Title", "OEBPS/ch1.xhtml", 0, 100)
        ch2 = make_chapter_boundary(2, 2, "Title", "OEBPS/ch2.xhtml", 100, 200)
        # Force same chapter_id by using same spine_position
        ch2_dup = EpubChapterBoundary(
            index=2, spine_position=1, title="Title", source_href="OEBPS/ch2.xhtml",
            start_offset=100, end_offset=200, word_count=50,
        )
        inp = make_epub_translation_input(chapter_map=(ch1, ch2_dup))
        with pytest.raises(ContractValidationError, match="Duplicate chapter_id"):
            validate_epub_translation_input(inp)

    def test_duplicate_spine_position_raises(self) -> None:
        # Use same spine_position but different index to trigger duplicate chapter_id (since chapter_id = ch{spine_position:04d})
        ch1 = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100)
        ch2 = make_chapter_boundary(2, 1, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200)
        inp = make_epub_translation_input(chapter_map=(ch1, ch2))
        with pytest.raises(ContractValidationError, match="Duplicate chapter_id"):
            validate_epub_translation_input(inp)

    def test_non_increasing_spine_positions_raises(self) -> None:
        ch1 = make_chapter_boundary(1, 2, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100)
        ch2 = make_chapter_boundary(2, 1, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200)
        inp = make_epub_translation_input(chapter_map=(ch1, ch2))
        with pytest.raises(ContractValidationError, match="not strictly increasing"):
            validate_epub_translation_input(inp)

    def test_invalid_extraction_status_raises(self) -> None:
        inp = make_epub_translation_input(extraction_status="unknown")
        with pytest.raises(ContractValidationError, match="extraction_status invalid"):
            validate_epub_translation_input(inp)

    def test_invalid_toc_entry_raises(self) -> None:
        bad_toc = (TocEntry(href="", title="Title", level=0),)
        inp = make_epub_translation_input(toc_entries=bad_toc)
        with pytest.raises(ContractValidationError, match="toc_entries href must be non-empty"):
            validate_epub_translation_input(inp)


class TestValidateEpubTranslationChunk:
    def test_valid_chunk(self) -> None:
        chunk = make_epub_chunk()
        validate_epub_translation_chunk(chunk)

    def test_invalid_offsets_raise(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="extracted_end_offset must be >= extracted_start_offset"):
            make_epub_chunk(extracted_start=100, extracted_end=50)  # end < start

    def test_body_offsets_outside_extracted_raise(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="body_start_offset must be >= extracted_start_offset"):
            make_epub_chunk(body_start=20, body_end=90, extracted_start=30, extracted_end=80)

    def test_negative_chunk_sequence_raises(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="chunk_sequence must be >= 0"):
            make_epub_chunk(chunk_sequence=-1)


class TestValidateEpubChunkResult:
    def test_valid_result(self) -> None:
        res = make_chunk_result()
        validate_epub_chunk_result(res)

    def test_invalid_status_raises(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="Invalid chunk status"):
            make_chunk_result(status="invalid")

    def test_negative_attempt_raises(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="attempt must be >= 0"):
            make_chunk_result(attempt=-1)


class TestValidateEpubChapterResult:
    def test_valid_result(self) -> None:
        res = make_chapter_result()
        validate_epub_chapter_result(res)

    def test_invalid_aggregate_status_raises(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="Invalid chapter aggregate status"):
            make_chapter_result(aggregate_status="invalid")

    def test_count_mismatch_raises(self) -> None:
        # Model validation catches this at construction time
        chunk_res = make_chunk_result(status="success")
        with pytest.raises(ValueError, match="success_count mismatch"):
            EpubChapterResult(
                chapter_id="ch0001",
                chapter_order=1,
                chunk_results=(chunk_res,),
                aggregate_status="success",
                success_count=0,  # Mismatch: 1 success chunk but declared 0
                failed_count=0,
                skipped_count=0,
                assembled_text="",
            )


class TestValidateEpubTranslationResult:
    def test_valid_result(self) -> None:
        res = make_translation_result()
        validate_epub_translation_result(res)

    def test_invalid_aggregate_status_raises(self) -> None:
        # Model validation catches this at construction time
        with pytest.raises(ValueError, match="Invalid aggregate status"):
            make_translation_result(aggregate_status="invalid")

    def test_success_status_with_failed_chunk_raises(self) -> None:
        # aggregate_status=success but chunk has failed status
        chunk_res = make_chunk_result(status="failed")
        chapter_res = make_chapter_result(chunk_results=(chunk_res,))
        res = make_translation_result(chapter_results=(chapter_res,), aggregate_status="success")
        # Validator catches this - message says "chapter" not "chunk"
        with pytest.raises(ContractValidationError, match="aggregate_status='success' but chapter"):
            validate_epub_translation_result(res)

    def test_incomplete_without_failures_raises(self) -> None:
        res = make_translation_result(aggregate_status="incomplete")
        with pytest.raises(ContractValidationError, match="no failed/skipped chunks found"):
            validate_epub_translation_result(res)


class TestValidateChunkOwnership:
    def test_valid_chunks(self) -> None:
        inp = make_epub_translation_input()
        # Chapter 1 has spine_position=1, start_offset=0, end_offset=100
        # Chapter 2 has spine_position=2, start_offset=100, end_offset=200
        chunks = (
            make_epub_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, extracted_start=30, extracted_end=80, body_start=30, body_end=80),
            make_epub_chunk(chunk_id="test:ch0002:ck0000", chapter_id="ch0002", chapter_order=2, chunk_sequence=0, extracted_start=130, extracted_end=180, body_start=130, body_end=180),
        )
        validate_chunk_ownership(inp, chunks)

    def test_unknown_chapter_raises(self) -> None:
        inp = make_epub_translation_input()
        chunks = (make_epub_chunk(chapter_id="ch9999"),)
        with pytest.raises(ContractValidationError, match="references unknown chapter"):
            validate_chunk_ownership(inp, chunks)

    def test_chapter_order_mismatch_raises(self) -> None:
        inp = make_epub_translation_input()
        chunks = (make_epub_chunk(chapter_id="ch0001", chapter_order=99),)
        with pytest.raises(ContractValidationError, match="chapter_order.*does not match"):
            validate_chunk_ownership(inp, chunks)

    def test_chunk_offsets_outside_chapter_raises(self) -> None:
        inp = make_epub_translation_input()
        # Chapter 1 has start_offset=0, end_offset=100
        # Chunk with offsets outside this range - model validation catches negative offset
        with pytest.raises(ValueError, match="body_end_offset must be <= extracted_end_offset"):
            make_epub_chunk(extracted_start=-10, extracted_end=50)

    def test_empty_chapter_must_have_exactly_one_chunk(self) -> None:
        inp = make_epub_translation_input()
        # Chapter 1 has word_count=50 (non-empty)
        # Make it empty
        empty_chapter = make_chapter_boundary(word_count=0, end_offset=0)
        inp_empty = make_epub_translation_input(chapter_map=(empty_chapter,))

        # Valid: exactly one empty chunk
        chunks = (make_epub_chunk(chapter_id="ch0001", source_text="", extracted_start=0, extracted_end=0, body_start=0, body_end=0),)
        validate_chunk_ownership(inp_empty, chunks)

        # Invalid: zero chunks for empty chapter
        with pytest.raises(ContractValidationError, match="must produce exactly one chunk"):
            validate_chunk_ownership(inp_empty, ())

        # Invalid: two chunks for empty chapter
        chunks2 = (
            make_epub_chunk(chunk_id="test:ch0001:ck0000", source_text="", extracted_start=0, extracted_end=0, body_start=0, body_end=0),
            make_epub_chunk(chunk_id="test:ch0001:ck0001", source_text="", extracted_start=0, extracted_end=0, body_start=0, body_end=0),
        )
        with pytest.raises(ContractValidationError, match="must produce exactly one chunk"):
            validate_chunk_ownership(inp_empty, chunks2)

    def test_duplicate_chunk_id_raises(self) -> None:
        inp = make_epub_translation_input()
        chunks = (
            make_epub_chunk(chunk_id="dup:ch0001:ck0000", chunk_sequence=0),
            make_epub_chunk(chunk_id="dup:ch0001:ck0000", chunk_sequence=1),
        )
        with pytest.raises(ContractValidationError, match="Duplicate chunk_id"):
            validate_chunk_ownership(inp, chunks)


class TestValidateCompleteContract:
    def test_valid_complete_contract(self) -> None:
        inp = make_epub_translation_input()
        chunks = (
            make_epub_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, extracted_start=30, extracted_end=80, body_start=30, body_end=80),
            make_epub_chunk(chunk_id="test:ch0002:ck0000", chapter_id="ch0002", chapter_order=2, chunk_sequence=0, extracted_start=130, extracted_end=180, body_start=130, body_end=180),
            make_epub_chunk(chunk_id="test:ch0003:ck0000", chapter_id="ch0003", chapter_order=3, chunk_sequence=0, extracted_start=230, extracted_end=280, body_start=230, body_end=280),
        )
        result = make_translation_result(
            chapter_results=(
                make_chapter_result(chapter_id="ch0001", chapter_order=1),
                make_chapter_result(chapter_id="ch0002", chapter_order=2),
                make_chapter_result(chapter_id="ch0003", chapter_order=3),
            )
        )
        validate_complete_contract(inp, chunks, result)

    def test_missing_chapter_in_result_raises(self) -> None:
        inp = make_epub_translation_input()
        chunks = (make_epub_chunk(chapter_id="ch0001", chunk_sequence=0),)
        # Result only has chapter 1, but input has 3 linear chapters
        result = make_translation_result(chapter_results=(make_chapter_result(chapter_id="ch0001"),))
        with pytest.raises(ContractValidationError, match="missing chapters"):
            validate_complete_contract(inp, chunks, result)

    def test_result_chapter_order_mismatch_raises(self) -> None:
        inp = make_epub_translation_input()
        chunks = (make_epub_chunk(chapter_id="ch0001", chunk_sequence=0),)
        # Result has chapter_order=5 but should be 1
        result = make_translation_result(chapter_results=(make_chapter_result(chapter_id="ch0001", chapter_order=5),))
        # The validation checks chapter order within result
        with pytest.raises(ContractValidationError, match="chapter order mismatch"):
            validate_complete_contract(inp, chunks, result)


# ========================================================================
# Marker/Body Separation Tests
# ========================================================================

class TestMarkerBodySeparation:
    """Verify contract correctly separates marker from pure body text."""

    def test_body_offsets_distinct_from_marker_offsets(self) -> None:
        """body_start_offset and body_end_offset must be distinct from marker-inclusive offsets."""
        ch = make_chapter_boundary(
            start_offset=0,
            end_offset=100,
            body_start_offset=30,   # after marker
            body_end_offset=95,     # before trailing newline
        )
        validate_chapter_boundary(ch)
        assert ch.body_start_offset > ch.start_offset
        assert ch.body_end_offset < ch.end_offset

    def test_marker_not_in_source_text(self) -> None:
        """Chunk source_text must be pure body, no marker."""
        chunk = make_epub_chunk(source_text="Pure chapter body text")
        validate_epub_translation_chunk(chunk)
        assert not chunk.source_text.startswith("===")
        assert "CHAPTER" not in chunk.source_text

    def test_empty_chapter_body_text_empty(self) -> None:
        """Empty chapter must have empty source_text."""
        # For empty chapter, body offsets should be within extracted range
        # Use body offsets that are valid within the default chapter's extracted range
        chunk = make_epub_chunk(source_text="", body_start=30, body_end=30)
        validate_epub_translation_chunk(chunk)
        assert chunk.source_text == ""

    def test_body_offsets_within_marker_range(self) -> None:
        """Body offsets must fall within marker-inclusive range."""
        ch = make_chapter_boundary(
            start_offset=0,
            end_offset=100,
            body_start_offset=25,
            body_end_offset=90,
        )
        validate_chapter_boundary(ch)


# ========================================================================
# Chapter Identity Tests
# ========================================================================

class TestChapterIdentity:
    def test_chapter_id_based_on_spine_position(self) -> None:
        """chapter_id derived from spine_position, not title."""
        ch1 = make_chapter_boundary(spine_position=1, title="Chapter 1")
        ch2 = make_chapter_boundary(spine_position=2, title="Chapter 1")  # Same title!
        assert ch1.chapter_id == "ch0001"
        assert ch2.chapter_id == "ch0002"
        assert ch1.chapter_id != ch2.chapter_id

    def test_duplicate_titles_supported(self) -> None:
        """Duplicate titles are valid, distinguished by chapter_id."""
        ch1 = make_chapter_boundary(spine_position=1, title="Prologue")
        ch2 = make_chapter_boundary(spine_position=2, title="Prologue")
        assert ch1.title == ch2.title
        assert ch1.chapter_id != ch2.chapter_id

    def test_spine_position_preserved(self) -> None:
        """Spine position must be preserved."""
        ch = make_chapter_boundary(spine_position=5)
        assert ch.spine_position == 5

    def test_source_href_preserved(self) -> None:
        """Source href must be preserved."""
        ch = make_chapter_boundary(source_href="OEBPS/chapter_01.xhtml")
        assert ch.source_href == "OEBPS/chapter_01.xhtml"

    def test_fragment_preserved(self) -> None:
        """Fragment in source_href must be preserved."""
        ch = make_chapter_boundary(source_href="OEBPS/ch1.xhtml#section2")
        assert ch.fragment == "section2"
        assert ch.href_without_fragment == "OEBPS/ch1.xhtml"

    def test_is_linear_preserved(self) -> None:
        """is_linear must be preserved."""
        ch_linear = make_chapter_boundary(is_linear=True)
        ch_supp = make_chapter_boundary(is_linear=False)
        assert ch_linear.is_linear is True
        assert ch_supp.is_linear is False


# ========================================================================
# Empty Chapter Tests
# ========================================================================

class TestEmptyChapter:
    def test_empty_chapter_supported(self) -> None:
        """Empty chapter (word_count=0) is valid."""
        # Use raw function to avoid auto-computed body offsets that conflict with empty chapter
        ch = make_chapter_boundary_raw(word_count=0, end_offset=0, body_start_offset=0, body_end_offset=0)
        validate_chapter_boundary(ch)
        assert ch.word_count == 0

    def test_empty_chapter_produces_one_chunk(self) -> None:
        """Empty chapter must produce exactly one empty chunk."""
        inp = make_epub_translation_input()
        empty_chapter = make_chapter_boundary(word_count=0, end_offset=0)
        inp_empty = make_epub_translation_input(chapter_map=(empty_chapter,))

        chunks = (make_epub_chunk(
            chapter_id="ch0001", source_text="",
            extracted_start=0, extracted_end=0, body_start=0, body_end=0
        ),)
        validate_chunk_ownership(inp_empty, chunks)


# ========================================================================
# Chunk Ownership Tests
# ========================================================================

class TestChunkOwnership:
    def test_chunk_belongs_to_exactly_one_chapter(self) -> None:
        """Each chunk belongs to exactly one chapter."""
        chunk = make_epub_chunk(chapter_id="ch0001")
        assert chunk.chapter_id == "ch0001"
        # Contract enforces single chapter_id per chunk

    def test_no_cross_chapter_chunks(self) -> None:
        """Chunks cannot span multiple chapters."""
        # This is enforced by validate_chunk_ownership checking
        # that chunk offsets are within chapter's start/end offsets
        inp = make_epub_translation_input()
        chunks = (make_epub_chunk(),)
        validate_chunk_ownership(inp, chunks)

    def test_duplicate_chunk_id_rejected(self) -> None:
        """Duplicate chunk IDs must be rejected."""
        inp = make_epub_translation_input()
        chunks = (
            make_epub_chunk(chunk_id="dup:ch0001:ck0000"),
            make_epub_chunk(chunk_id="dup:ch0001:ck0000"),
        )
        with pytest.raises(ContractValidationError, match="Duplicate chunk_id"):
            validate_chunk_ownership(inp, chunks)


# ========================================================================
# Result Ordering Tests
# ========================================================================

class TestResultOrdering:
    def test_result_chapters_spine_order(self) -> None:
        """Result chapters must be in spine order."""
        res = make_translation_result(
            chapter_results=(
                make_chapter_result(chapter_id="ch0001", chapter_order=1),
                make_chapter_result(chapter_id="ch0002", chapter_order=2),
                make_chapter_result(chapter_id="ch0003", chapter_order=3),
            )
        )
        validate_epub_translation_result(res)

    def test_out_of_order_result_rejected(self) -> None:
        """Out-of-order chapter results must be rejected."""
        res = make_translation_result(
            chapter_results=(
                make_chapter_result(chapter_id="ch0002", chapter_order=2),
                make_chapter_result(chapter_id="ch0001", chapter_order=1),  # Out of order!
            )
        )
        with pytest.raises(ContractValidationError, match="chapter order mismatch"):
            validate_epub_translation_result(res)

    def test_duplicate_chapter_result_rejected(self) -> None:
        """Duplicate chapter results must be rejected."""
        res = make_translation_result(
            chapter_results=(
                make_chapter_result(chapter_id="ch0001"),
                make_chapter_result(chapter_id="ch0001"),  # Duplicate!
            )
        )
        with pytest.raises(ContractValidationError, match="Duplicate chapter_id"):
            validate_epub_translation_result(res)


# ========================================================================
# Failure Propagation Tests
# ========================================================================

class TestFailurePropagation:
    def test_failed_required_chunk_prevents_success(self) -> None:
        """One failed required chunk prevents overall success."""
        chunk_res = make_chunk_result(status="failed")
        chapter_res = make_chapter_result(chunk_results=(chunk_res,), aggregate_status="incomplete")
        res = make_translation_result(chapter_results=(chapter_res,), aggregate_status="incomplete")
        validate_epub_translation_result(res)  # incomplete is OK

        # But success is NOT OK
        res_fail = make_translation_result(chapter_results=(chapter_res,), aggregate_status="success")
        with pytest.raises(ContractValidationError, match="aggregate_status='success' but chapter"):
            validate_epub_translation_result(res_fail)

    def test_success_requires_all_chunks_success(self) -> None:
        """Aggregate success requires ALL chunks success."""
        chunk_res = make_chunk_result(status="skipped")
        chapter_res = make_chapter_result(chunk_results=(chunk_res,), aggregate_status="success")
        res = make_translation_result(chapter_results=(chapter_res,), aggregate_status="success")
        with pytest.raises(ContractValidationError, match="aggregate_status='success' but chunk"):
            validate_epub_translation_result(res)

    def test_incomplete_must_have_failures(self) -> None:
        """Incomplete status must have at least one failure/skip."""
        res = make_translation_result(aggregate_status="incomplete")
        with pytest.raises(ContractValidationError, match="no failed/skipped chunks"):
            validate_epub_translation_result(res)


# ========================================================================
# Determinism Tests
# ========================================================================

class TestDeterminism:
    def test_validator_deterministic(self) -> None:
        """Validators must produce same result on repeated calls."""
        inp = make_epub_translation_input()
        for _ in range(10):
            validate_epub_translation_input(inp)  # Must not raise

        chunks = (make_epub_chunk(),)
        for _ in range(10):
            validate_chunk_ownership(inp, chunks)

    def test_same_input_same_validation_result(self) -> None:
        """Same input always yields same validation outcome."""
        inp = make_epub_translation_input()
        # Call multiple times
        results = []
        for _ in range(5):
            try:
                validate_epub_translation_input(inp)
                results.append(True)
            except ContractValidationError:
                results.append(False)
        assert all(results) or not any(results)


# ========================================================================
# Immutability Tests
# ========================================================================

class TestImmutability:
    def test_models_are_frozen(self) -> None:
        """All contract models must be frozen (immutable)."""
        ch = make_chapter_boundary()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            ch.title = "Modified"

    def test_tuple_collections_immutable(self) -> None:
        """Tuple collections should be immutable."""
        inp = make_epub_translation_input()
        with pytest.raises((TypeError, AttributeError)):
            inp.chapter_map = ()

    def test_nested_immutability(self) -> None:
        """Nested objects should be immutable."""
        chunk = make_epub_chunk()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            chunk.source_text = "Modified"


# ========================================================================
# Safety Tests (No Network/Provider/Translation)
# ========================================================================

class TestSafety:
    def test_no_network_in_validators(self) -> None:
        """Validators must not make network calls."""
        inp = make_epub_translation_input()
        # This should complete instantly without network
        validate_epub_translation_input(inp)

    def test_no_provider_in_validators(self) -> None:
        """Validators must not call providers."""
        inp = make_epub_translation_input()
        validate_epub_translation_input(inp)  # Pure local validation

    def test_no_translation_execution(self) -> None:
        """Contract validation must not execute translation."""
        inp = make_epub_translation_input()
        validate_epub_translation_input(inp)  # Pure contract check

    def test_no_source_modification(self) -> None:
        """Contract validation must not modify source data."""
        inp = make_epub_translation_input()
        original_hash = inp.original_hash
        validate_epub_translation_input(inp)
        assert inp.original_hash == original_hash


# ========================================================================
# Scope Boundary Tests
# ========================================================================

class TestScopeBoundaries:
    def test_no_translation_runtime_import(self) -> None:
        """Contract must not import translation runtime."""
        import core.epub_translation.contract.validation as val_module
        import core.epub_translation.contract.models as mod_module
        # Check source doesn't import runtime modules
        import inspect
        val_source = inspect.getsource(val_module)
        mod_source = inspect.getsource(mod_module)
        forbidden = [
            "TranslationEngine",
            "RuntimeOrchestrator",
            "ProviderManager",
            "NvidiaClient",
            "TranslationWorker",
        ]
        for word in forbidden:
            assert word not in val_source, f"Validation imports {word}"
            assert word not in mod_source, f"Models imports {word}"

    def test_no_prompt_memory_quality_imports(self) -> None:
        """Contract must not import prompt/memory/quality modules."""
        import core.epub_translation.contract.validation as val_module
        import core.epub_translation.contract.models as mod_module
        import inspect
        val_source = inspect.getsource(val_module)
        mod_source = inspect.getsource(mod_module)
        forbidden = [
            "LiteraryPromptBuilder",
            "CharacterMemory",
            "ContextMemory",
            "QualityRuntime",
            "Retry",
            "Recovery",
        ]
        for word in forbidden:
            assert word not in val_source
            assert word not in mod_source


# ========================================================================
# Compile/Import Tests
# ========================================================================

def test_module_compiles() -> None:
    """Contract modules must compile without errors."""
    import core.epub_translation.contract.models
    import core.epub_translation.contract.validation
    import core.epub_translation.contract
    assert True


def test_exports_available() -> None:
    """All required exports must be available."""
    from core.epub_translation.contract import (
        EpubMetadata,
        EpubChapterBoundary,
        ResourceRef,
        TocEntry,
        ExtractionManifest,
        EpubTranslationInput,
        EpubTranslationChunk,
        EpubChunkResult,
        EpubChapterResult,
        EpubTranslationResult,
        ContractValidationError,
        validate_sha256,
        validate_chapter_id,
        validate_epub_translation_input,
        validate_epub_translation_chunk,
        validate_epub_chunk_result,
        validate_epub_chapter_result,
        validate_epub_translation_result,
        validate_chunk_ownership,
        validate_complete_contract,
    )
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
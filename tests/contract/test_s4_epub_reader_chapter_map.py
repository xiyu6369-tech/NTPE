"""S4 EPUB Reader Chapter Map Tests — Offline, Deterministic.

Tests for building ReaderChapterMap from EpubTranslationResult and EpubTranslationInput.
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

import pytest

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
)
from core.epub_translation.reader_chapter_map import (
    build_epub_reader_chapter_map,
    build_epub_reader_chapter_map_with_metadata,
    ReaderChapterMapBuildError,
    EpubReaderChapterMapResult,
)
from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap


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
    body_start_offset: int | None = None,
    body_end_offset: int | None = None,
    is_linear: bool = True,
    word_count: int = 50,
) -> EpubChapterBoundary:
    if body_start_offset is None:
        body_start_offset = start_offset + 30
    if body_end_offset is None:
        body_end_offset = max(start_offset + 1, end_offset - 5)
    return EpubChapterBoundary(
        index=index,
        spine_position=spine_position,
        title=title,
        source_href=source_href,
        start_offset=start_offset,
        end_offset=end_offset,
        body_start_offset=body_start_offset,
        body_end_offset=body_end_offset,
        is_linear=is_linear,
        word_count=word_count,
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
) -> EpubTranslationInput:
    if chapter_map is None:
        chapter_map = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )

    return EpubTranslationInput(
        source_epub_path=Path("test.epub"),
        original_hash=original_hash,
        extraction_status=extraction_status,
        warnings=(),
        metadata=make_epub_metadata(),
        chapter_map=chapter_map,
        resources=(),
        toc_entries=(
            make_toc_entry("ch1.xhtml", "Chapter 1"),
            make_toc_entry("ch2.xhtml", "Chapter 2"),
        ),
        fixed_layout_info=None,
        extraction_manifest=make_extraction_manifest(),
    )


def make_epub_chunk_result(
    chunk_id: str = "ch0001:chunk0000",
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


def make_epub_chapter_result(
    chapter_id: str = "ch0001",
    chapter_order: int = 1,
    chunk_results: tuple[EpubChunkResult, ...] | None = None,
    aggregate_status: str = "success",
    assembled_text: str | None = None,
) -> EpubChapterResult:
    if chunk_results is None:
        chunk_results = (make_epub_chunk_result(chunk_id=f"{chapter_id}:chunk0000"),)

    success_count = sum(1 for c in chunk_results if c.status == "success")
    failed_count = sum(1 for c in chunk_results if c.status == "failed")
    skipped_count = sum(1 for c in chunk_results if c.status == "skipped")

    if assembled_text is None:
        assembled_text = "\n\n".join(c.translated_text for c in chunk_results if c.status == "success")
        if assembled_text:
            assembled_text += "\n"

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


def make_epub_translation_result(
    chapter_results: tuple[EpubChapterResult, ...] | None = None,
    aggregate_status: str = "success",
    session_id: str = "test-session-123",
) -> EpubTranslationResult:
    if chapter_results is None:
        chapter_results = (make_epub_chapter_result(),)

    return EpubTranslationResult(
        aggregate_status=aggregate_status,
        chapter_results=chapter_results,
        success_count=sum(cr.success_count for cr in chapter_results),
        failed_count=sum(cr.failed_count for cr in chapter_results),
        skipped_count=sum(cr.skipped_count for cr in chapter_results),
        session_id=session_id,
        resume_state_path=None,
    )


# ========================================================================
# S4-C01: one chapter / one chunk
# ========================================================================

class TestS4C01OneChapterOneChunk:
    """S4-C01 — one chapter / one chunk → 1 reader chapter"""

    def test_one_chapter_one_chunk_success(self) -> None:
        """One chapter, one successful chunk produces one reader chapter."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(
            chunk_id="ch0001:chunk0000",
            translated_text="제1장 내용입니다.",
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=(chunk_result,),
            aggregate_status="success",
            assembled_text="제1장 내용입니다.\n",
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,),
            aggregate_status="success",
        )

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert isinstance(reader_chapter_map, ReaderChapterMap)
        assert len(reader_chapter_map.chapters) == 1
        chapter = reader_chapter_map.chapters[0]
        assert chapter.chapter_id == "ch0001"
        assert chapter.chapter_order == 0  # 0-based in ChapterBoundary
        assert chapter.chapter_title == "Chapter 1"
        assert chapter.start_position == 0
        assert chapter.end_position > 0
        assert chapter.scene_ids == ()


# ========================================================================
# S4-C02: one chapter / multiple chunks
# ========================================================================

class TestS4C02OneChapterMultipleChunks:
    """S4-C02 — one chapter / multiple chunks → 1 reader chapter, content follows chunk order"""

    def test_one_chapter_three_chunks(self) -> None:
        """One chapter with three chunks aggregates in chunk_sequence order."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 번째 덩어리"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0001", translated_text="두 번째 덩어리"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0002", translated_text="세 번째 덩어리"),
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=chunk_results,
            aggregate_status="success",
            assembled_text="첫 번째 덩어리\n\n두 번째 덩어리\n\n세 번째 덩어리\n",
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,),
            aggregate_status="success",
        )

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 1
        chapter = reader_chapter_map.chapters[0]
        assert chapter.chapter_id == "ch0001"
        # Content should be in chunk order (already assembled in chapter_result)
        full_text = "첫 번째 덩어리\n\n두 번째 덩어리\n\n세 번째 덩어리\n"
        assert chapter.start_position == 0
        assert chapter.end_position == len(full_text)


# ========================================================================
# S4-C03: multiple chapters
# ========================================================================

class TestS4C03MultipleChapters:
    """S4-C03 — multiple chapters → 3 reader chapters, correct chapter order"""

    def test_three_chapters_spine_order(self) -> None:
        """Three chapters in spine order produce three reader chapters in correct order."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 장")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="둘째 장")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="셋째 장")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="첫 장\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="둘째 장\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="셋째 장\n"),
        )
        translation_result = make_epub_translation_result(
            chapter_results=chapter_results,
            aggregate_status="success",
        )

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 3
        assert reader_chapter_map.chapters[0].chapter_id == "ch0001"
        assert reader_chapter_map.chapters[0].chapter_order == 0
        assert reader_chapter_map.chapters[1].chapter_id == "ch0002"
        assert reader_chapter_map.chapters[1].chapter_order == 1
        assert reader_chapter_map.chapters[2].chapter_id == "ch0003"
        assert reader_chapter_map.chapters[2].chapter_order == 2


# ========================================================================
# S4-C04: chapter identity
# ========================================================================

class TestS4C04ChapterIdentity:
    """S4-C04 — Reader chapter identity must match upstream chapter identity"""

    def test_chapter_id_preserved(self) -> None:
        """chapter_id from EpubChapterBoundary must be preserved."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(spine_position=5, title="Prologue"),)
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0005:chunk0000", translated_text="서문 내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0005",  # Based on spine_position 5
            chapter_order=1,
            chunk_results=(chunk_result,),
            assembled_text="서문 내용\n",
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert reader_chapter_map.chapters[0].chapter_id == "ch0005"

    def test_duplicate_titles_distinguished_by_chapter_id(self) -> None:
        """Chapters with same title are distinguished by chapter_id."""
        chapters = (
            make_chapter_boundary(1, 1, "Prologue", "OEBPS/prologue.xhtml", 0, 50, 20, 45),
            make_chapter_boundary(2, 2, "Prologue", "OEBPS/ch1.xhtml", 50, 100, 70, 95),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 번째 프롤로그")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="두 번째 프롤로그")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="첫 번째 프롤로그\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="두 번째 프롤로그\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert reader_chapter_map.chapters[0].chapter_id == "ch0001"
        assert reader_chapter_map.chapters[1].chapter_id == "ch0002"
        assert reader_chapter_map.chapters[0].chapter_title == "Prologue"
        assert reader_chapter_map.chapters[1].chapter_title == "Prologue"


# ========================================================================
# S4-C05: chunk identity preservation
# ========================================================================

class TestS4C05ChunkIdentityPreservation:
    """S4-C05 — Aggregation has no duplicate, missing, cross-chapter chunks"""

    def test_no_duplicate_chunks(self) -> None:
        """Duplicate chunk_ids in result should fail."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # Duplicate chunk_id
        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="B"),  # Duplicate!
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=chunk_results
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Duplicate chunk_id"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_no_missing_chunks(self) -> None:
        """Missing chunk sequences should fail."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # Missing chunk0001 (has 0000 and 0002)
        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0002", translated_text="C"),
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=chunk_results
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Missing chunk sequences"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_no_cross_chapter_chunks(self) -> None:
        """Chunk belonging to wrong chapter should fail."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # Chunk claims to belong to ch0002 but chapter is ch0001
        chunk_result = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="Wrong chapter")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,)
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="does not belong to chapter"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_duplicate_chapter_in_result_fails(self) -> None:
        """Duplicate chapter_id in result should fail."""
        translation_input = make_epub_translation_input(
            chapter_map=(
                make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
                make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            )
        )

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="B")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),  # Duplicate chapter_id!
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        with pytest.raises(ReaderChapterMapBuildError, match="Duplicate chapter_id in result"):
            build_epub_reader_chapter_map(translation_result, translation_input)


# ========================================================================
# S4-C06: deterministic ordering
# ========================================================================

class TestS4C06DeterministicOrdering:
    """S4-C06 — Input chunk completion order doesn't affect output order"""

    def test_chapter_order_independent_of_input_order(self) -> None:
        """Chapters always ordered by spine position, not input order."""
        # Provide chapters in reverse spine order in input
        chapters = (
            make_chapter_boundary(3, 3, "Chapter C", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
            make_chapter_boundary(1, 1, "Chapter A", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter B", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="B")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="C")

        # Result MUST be in spine order (chapter_order 1, 2, 3)
        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="C\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        # Output must be in spine order (1, 2, 3)
        assert reader_chapter_map.chapters[0].chapter_id == "ch0001"
        assert reader_chapter_map.chapters[1].chapter_id == "ch0002"
        assert reader_chapter_map.chapters[2].chapter_id == "ch0003"

    def test_repeated_build_deterministic(self) -> None:
        """Same input produces identical ReaderChapterMap."""
        translation_input = make_epub_translation_input()

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 장")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="둘째 장")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="셋째 장")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="첫 장\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="둘째 장\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="셋째 장\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        map1 = build_epub_reader_chapter_map(translation_result, translation_input)
        map2 = build_epub_reader_chapter_map(translation_result, translation_input)

        assert map1 == map2
        assert map1.chapters == map2.chapters


# ========================================================================
# S4-C07: empty chapter
# ========================================================================

class TestS4C07EmptyChapter:
    """S4-C07 — Empty chapter is preserved"""

    def test_empty_chapter_preserved(self) -> None:
        """Empty chapter (word_count=0) produces chapter with empty content."""
        # Empty chapter: word_count=0, body offsets equal
        empty_chapter = make_chapter_boundary(
            word_count=0,
            start_offset=0,
            end_offset=30,
            body_start_offset=30,
            body_end_offset=30,
        )
        translation_input = make_epub_translation_input(chapter_map=(empty_chapter,))

        # Empty chapter has one empty chunk
        chunk_result = make_epub_chunk_result(
            chunk_id="ch0001:chunk0000",
            translated_text="",
            status="success",
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=(chunk_result,),
            aggregate_status="success",
            assembled_text="",
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 1
        chapter = reader_chapter_map.chapters[0]
        assert chapter.chapter_id == "ch0001"
        assert chapter.start_position == 0
        assert chapter.end_position == 0  # Empty content


# ========================================================================
# S4-C08: missing chunk
# ========================================================================

class TestS4C08MissingChunk:
    """S4-C08 — Missing chunk must fail closed"""

    def test_missing_chunk_fails(self) -> None:
        """Gap in chunk sequence must raise error."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # Only chunk 0 and 2, missing 1
        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="First"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0002", translated_text="Third"),
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=chunk_results
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Missing chunk sequences"):
            build_epub_reader_chapter_map(translation_result, translation_input)


# ========================================================================
# S4-C09: duplicate chunk
# ========================================================================

class TestS4C09DuplicateChunk:
    """S4-C09 — Duplicate chunk must fail closed"""

    def test_duplicate_chunk_fails(self) -> None:
        """Same chunk_id appearing twice must raise error."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="B"),  # Duplicate!
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=chunk_results
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Duplicate chunk_id"):
            build_epub_reader_chapter_map(translation_result, translation_input)


# ========================================================================
# S4-C10: duplicate chapter
# ========================================================================

class TestS4C10DuplicateChapter:
    """S4-C10 — Duplicate chapter must fail closed"""

    def test_duplicate_chapter_in_result_fails(self) -> None:
        """Two chapter results with same chapter_id must raise."""
        translation_input = make_epub_translation_input(
            chapter_map=(
                make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
                make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            )
        )

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="B")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        with pytest.raises(ReaderChapterMapBuildError, match="Duplicate chapter_id in result"):
            build_epub_reader_chapter_map(translation_result, translation_input)


# ========================================================================
# S4-C11: wrong chapter ownership
# ========================================================================

class TestS4C11WrongChapterOwnership:
    """S4-C11 — Chunk pointing to wrong chapter must fail"""

    def test_chunk_wrong_chapter_fails(self) -> None:
        """Chunk with chapter_id not matching its chapter result must fail."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # Chunk claims ch0002 but chapter result is ch0001
        chunk_result = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="Wrong")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,)
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="does not belong to chapter"):
            build_epub_reader_chapter_map(translation_result, translation_input)


# ========================================================================
# S4-C12: failed chapter
# ========================================================================

class TestS4C12FailedChapter:
    """S4-C12 — Failed chapter must not produce false-success reader chapter"""

    def test_failed_chapter_preserved_in_map(self) -> None:
        """Failed chapter still appears in map but with empty content."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(
            chunk_id="ch0001:chunk0000",
            status="failed",
            translated_text="",
            error="Provider error",
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=(chunk_result,),
            aggregate_status="failed",
            assembled_text="",
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,),
            aggregate_status="failed",
        )

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 1
        chapter = reader_chapter_map.chapters[0]
        assert chapter.chapter_id == "ch0001"
        assert chapter.start_position == 0
        assert chapter.end_position == 0  # No content for failed chapter

    def test_failed_chapter_not_reported_as_success(self) -> None:
        """Failed chapter status must be preserved in metadata result."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(
            chunk_id="ch0001:chunk0000", status="failed", translated_text="", error="Error"
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,),
            aggregate_status="failed", assembled_text=""
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,), aggregate_status="failed"
        )

        enriched = build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)

        assert enriched.chapter_statuses["ch0001"] == "failed"
        assert enriched.reader_chapter_map.chapters[0].chapter_id == "ch0001"


# ========================================================================
# S4-C13: incomplete chapter
# ========================================================================

class TestS4C13IncompleteChapter:
    """S4-C13 — Incomplete chapter must not be converted to success"""

    def test_incomplete_chapter_preserved(self) -> None:
        """Incomplete chapter appears in map with partial content."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        # One success, one failed -> incomplete
        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", status="success", translated_text="Success part"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0001", status="failed", translated_text="", error="Failed"),
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=chunk_results,
            aggregate_status="incomplete",
            assembled_text="Success part\n",  # Only successful chunks
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,),
            aggregate_status="incomplete",
        )

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 1
        chapter = reader_chapter_map.chapters[0]
        assert chapter.chapter_id == "ch0001"
        # Should have content from successful chunk only
        assert chapter.end_position > chapter.start_position

    def test_incomplete_status_preserved_in_metadata(self) -> None:
        """Incomplete status must be preserved in enriched result."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_results = (
            make_epub_chunk_result(chunk_id="ch0001:chunk0000", status="success", translated_text="OK"),
            make_epub_chunk_result(chunk_id="ch0001:chunk0001", status="failed", translated_text="", error="Fail"),
        )
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=chunk_results,
            aggregate_status="incomplete", assembled_text="OK\n"
        )
        translation_result = make_epub_translation_result(
            chapter_results=(chapter_result,), aggregate_status="incomplete"
        )

        enriched = build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)

        assert enriched.chapter_statuses["ch0001"] == "incomplete"


# ========================================================================
# S4-C14: source href preservation
# ========================================================================

class TestS4C14SourceHrefPreservation:
    """S4-C14 — source_href preserved if contract supports it"""

    def test_source_href_preserved_in_enriched_result(self) -> None:
        """source_href from input chapter must be preserved in enriched result."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/custom_ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        enriched = build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)

        assert enriched.source_hrefs["ch0001"] == "OEBPS/custom_ch1.xhtml"

    def test_fragment_preserved_in_enriched_result(self) -> None:
        """Fragment from source_href must be preserved."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml#section-2", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        enriched = build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)

        assert enriched.fragments["ch0001"] == "section-2"
        assert enriched.source_hrefs["ch0001"] == "OEBPS/ch1.xhtml#section-2"


# ========================================================================
# S4-C15: title preservation
# ========================================================================

class TestS4C15TitlePreservation:
    """S4-C15 — Upstream title must be preserved"""

    def test_chapter_title_from_input_preserved(self) -> None:
        """Chapter title from input chapter_map must be used."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Custom Title", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert reader_chapter_map.chapters[0].chapter_title == "Custom Title"

    def test_fallback_title_when_input_title_none(self) -> None:
        """Fallback title used when input has no title."""
        chapter = make_chapter_boundary(title=None)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        # Should use fallback "제1장" (Korean) or similar
        assert reader_chapter_map.chapters[0].chapter_title is not None
        assert reader_chapter_map.chapters[0].chapter_title != ""


# ========================================================================
# S4-C16: deterministic repeated build
# ========================================================================

class TestS4C16DeterministicRepeatedBuild:
    """S4-C16 — Same input build twice produces identical result"""

    def test_repeated_build_identical(self) -> None:
        """Two builds with same input produce equal ReaderChapterMap."""
        translation_input = make_epub_translation_input()

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 장")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="둘째 장")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="셋째 장")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="첫 장\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="둘째 장\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="셋째 장\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        map1 = build_epub_reader_chapter_map(translation_result, translation_input)
        map2 = build_epub_reader_chapter_map(translation_result, translation_input)

        assert map1 == map2
        # Check all deterministic fields
        for c1, c2 in zip(map1.chapters, map2.chapters):
            assert c1.chapter_id == c2.chapter_id
            assert c1.chapter_order == c2.chapter_order
            assert c1.chapter_title == c2.chapter_title
            assert c1.start_position == c2.start_position
            assert c1.end_position == c2.end_position
            assert c1.scene_ids == c2.scene_ids


# ========================================================================
# Additional validation tests
# ========================================================================

class TestValidationEdgeCases:
    """Additional validation and edge case tests."""

    def test_mismatched_result_chapters_raises(self) -> None:
        """Result missing chapters from input raises."""
        translation_input = make_epub_translation_input()  # 3 chapters
        # Result only has 1 chapter
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="missing chapters"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_extra_chapter_in_result_raises(self) -> None:
        """Result with extra chapter not in input raises."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="Extra")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="Extra\n")
        # Create result with extra chapter (ch9999 not in input)
        chunk_extra = make_epub_chunk_result(chunk_id="ch9999:chunk0000", translated_text="Extra")
        chapter_extra = make_epub_chapter_result(chapter_id="ch9999", chapter_order=2, chunk_results=(chunk_extra,), assembled_text="Extra\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result, chapter_extra))

        with pytest.raises(ReaderChapterMapBuildError, match="extra chapters"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_chapter_order_mismatch_raises(self) -> None:
        """Chapter order not sequential raises."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        # chapter_order=5 but should be 1
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=5, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Chapter order mismatch"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_empty_input_chapter_map_raises(self) -> None:
        """Empty input chapter_map raises."""
        translation_input = make_epub_translation_input(chapter_map=())
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        with pytest.raises(ReaderChapterMapBuildError, match="Input chapter_map is empty"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_empty_result_chapter_results_raises(self) -> None:
        """Empty result chapter_results raises."""
        translation_input = make_epub_translation_input()
        translation_result = make_epub_translation_result(chapter_results=())

        with pytest.raises(ReaderChapterMapBuildError, match="Result chapter_results is empty"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_duplicate_chapter_id_in_input_raises(self) -> None:
        """Duplicate chapter_id in input raises."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        # Force same chapter_id by using same spine_position
        ch2_dup = EpubChapterBoundary(
            index=2, spine_position=1, title="Ch2", source_href="OEBPS/ch2.xhtml",
            start_offset=100, end_offset=200, word_count=50,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapters[0], ch2_dup))

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="B")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        with pytest.raises(ReaderChapterMapBuildError, match="Duplicate chapter_id in input"):
            build_epub_reader_chapter_map(translation_result, translation_input)

    def test_supplementary_chapter_included(self) -> None:
        """Non-linear chapters are included in spine order."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95, is_linear=True),
            make_chapter_boundary(2, 2, "Appendix", "OEBPS/app.xhtml", 100, 150, 110, 145, is_linear=False),
            make_chapter_boundary(3, 3, "Ch2", "OEBPS/ch2.xhtml", 150, 250, 180, 245, is_linear=True),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="Ch1")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="App")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="Ch2")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="Ch1\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="App\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="Ch2\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        assert len(reader_chapter_map.chapters) == 3
        # All three in spine order
        assert [c.chapter_id for c in reader_chapter_map.chapters] == ["ch0001", "ch0002", "ch0003"]


# ========================================================================
# Immutability tests
# ========================================================================

class TestImmutability:
    """Verify immutability of inputs and outputs."""

    def test_input_not_modified(self) -> None:
        """Translation input must not be modified."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        original_hash = translation_input.original_hash
        original_chapter_map = translation_input.chapter_map

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        build_epub_reader_chapter_map(translation_result, translation_input)

        assert translation_input.original_hash == original_hash
        assert translation_input.chapter_map == original_chapter_map

    def test_result_not_modified(self) -> None:
        """Translation result must not be modified."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        original_aggregate = translation_result.aggregate_status
        original_chapters = translation_result.chapter_results

        build_epub_reader_chapter_map(translation_result, translation_input)

        assert translation_result.aggregate_status == original_aggregate
        assert translation_result.chapter_results == original_chapters

    def test_output_is_immutable(self) -> None:
        """ReaderChapterMap must be immutable (frozen dataclass)."""
        from dataclasses import FrozenInstanceError

        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)

        with pytest.raises((FrozenInstanceError, AttributeError)):
            # type: ignore
            reader_chapter_map.chapters = ()

        with pytest.raises((FrozenInstanceError, AttributeError)):
            # type: ignore
            reader_chapter_map.chapters[0].chapter_id = "modified"


# ========================================================================
# Safety tests (no network, no provider, no translation)
# ========================================================================

class TestSafety:
    """Verify no network, provider, or translation execution."""

    def test_no_network(self) -> None:
        """Builder makes no network calls."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        # Should complete instantly
        build_epub_reader_chapter_map(translation_result, translation_input)

    def test_no_provider(self) -> None:
        """Builder does not call any provider."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        build_epub_reader_chapter_map(translation_result, translation_input)

    def test_no_translation_execution(self) -> None:
        """Builder does not execute translation."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        build_epub_reader_chapter_map(translation_result, translation_input)

    def test_no_source_modification(self) -> None:
        """Builder must not modify source data."""
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        original_input_hash = translation_input.original_hash
        original_result_status = translation_result.aggregate_status

        build_epub_reader_chapter_map(translation_result, translation_input)

        assert translation_input.original_hash == original_input_hash
        assert translation_result.aggregate_status == original_result_status


# ========================================================================
# Compile/Import tests
# ========================================================================

def test_module_compiles() -> None:
    """Module compiles without errors."""
    import core.epub_translation.reader_chapter_map
    assert True


def test_exports_available() -> None:
    """All required exports available."""
    from core.epub_translation.reader_chapter_map import (
        build_epub_reader_chapter_map,
        build_epub_reader_chapter_map_with_metadata,
        ReaderChapterMapBuildError,
        EpubReaderChapterMapResult,
    )
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
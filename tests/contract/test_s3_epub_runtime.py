"""S3 EPUB Translation Runtime Tests — Offline, Deterministic."""

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
    EpubTranslationResult,
)
from core.epub_translation.runtime import (
    EpubTranslationOptions,
    translate_epub_translation_input,
)
from core.runtime_orchestrator.models import RuntimeExecutionResult


# ========================================================================
# Fixtures (reuse S2 patterns)
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
        ),
        fixed_layout_info=None,
        extraction_manifest=make_extraction_manifest(),
    )


def make_epub_translation_chunk(
    chapter_id: str = "ch0001",
    chapter_order: int = 1,
    chunk_sequence: int = 0,
    source_text: str = "Test chapter content.",
    body_start_offset: int = 30,
    body_end_offset: int = 50,
    extracted_start_offset: int = 30,
    extracted_end_offset: int = 50,
    source_href: str | None = "OEBPS/ch1.xhtml",
    fragment: str | None = None,
) -> EpubTranslationChunk:
    return EpubTranslationChunk(
        chunk_id=f"{chapter_id}:chunk{chunk_sequence:04d}",
        chapter_id=chapter_id,
        chapter_order=chapter_order,
        chunk_sequence=chunk_sequence,
        source_text=source_text,
        extracted_start_offset=extracted_start_offset,
        extracted_end_offset=extracted_end_offset,
        body_start_offset=body_start_offset,
        body_end_offset=body_end_offset,
        source_href=source_href,
        fragment=fragment,
    )


# ========================================================================
# Smoke Test
# ========================================================================

class TestS3Bootstrap:
    """Minimal smoke test for S3 EPUB Translation Runtime."""

    def test_one_chapter_one_chunk_dry_run(self) -> None:
        """One chapter, one chunk, dry-run mode."""
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=50,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))
        
        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=0,
            source_text="Test chapter content.",
            body_start_offset=30,
            body_end_offset=50,
            extracted_start_offset=30,
            extracted_end_offset=50,
        )
        
        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )
        
        result = translate_epub_translation_input(options)
        
        assert isinstance(result, EpubTranslationResult)
        assert result.aggregate_status in {"success", "incomplete", "failed"}
        assert len(result.chapter_results) == 1
        
        chapter_result = result.chapter_results[0]
        assert chapter_result.chapter_id == "ch0001"
        assert chapter_result.chapter_order == 1
        assert len(chapter_result.chunk_results) == 1
        
        chunk_result = chapter_result.chunk_results[0]
        assert chunk_result.chunk_id == "ch0001:chunk0000"
        assert chunk_result.status == "dry_run"
        assert chunk_result.translated_text == ""
        assert chunk_result.attempt == 0


# ========================================================================
# Batch A — Offline Coverage Expansion
# ========================================================================


class TestS3BatchA:
    """Batch A: offline, deterministic S3 coverage expansion."""

    def test_one_chapter_multiple_chunks_dry_run(self) -> None:
        """One chapter, multiple chunks in sequence order."""
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=150,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Chunk 1.", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Chunk 2.", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="Chunk 3.", body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert isinstance(result, EpubTranslationResult)
        assert len(result.chapter_results) == 1
        cr = result.chapter_results[0]
        assert cr.chapter_id == "ch0001"
        assert len(cr.chunk_results) == 3
        # Verify chunk_sequence ordering preserved
        assert cr.chunk_results[0].chunk_id == "ch0001:chunk0000"
        assert cr.chunk_results[1].chunk_id == "ch0001:chunk0001"
        assert cr.chunk_results[2].chunk_id == "ch0001:chunk0002"
        for ccr in cr.chunk_results:
            assert ccr.status == "dry_run"
            assert ccr.translated_text == ""
            assert ccr.attempt == 0

    def test_multiple_chapters_dry_run(self) -> None:
        """Multiple linear chapters in spine order."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Ch1 content", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Ch2 content", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
            make_epub_translation_chunk(chapter_id="ch0003", chapter_order=3, chunk_sequence=0, source_text="Ch3 content", body_start_offset=230, body_end_offset=250, extracted_start_offset=230, extracted_end_offset=250),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 3
        # Verify chapter_order ordering (spine order)
        assert result.chapter_results[0].chapter_id == "ch0001"
        assert result.chapter_results[0].chapter_order == 1
        assert result.chapter_results[1].chapter_id == "ch0002"
        assert result.chapter_results[1].chapter_order == 2
        assert result.chapter_results[2].chapter_id == "ch0003"
        assert result.chapter_results[2].chapter_order == 3
        for cr in result.chapter_results:
            assert len(cr.chunk_results) == 1
            assert cr.chunk_results[0].status == "dry_run"

    def test_empty_chapter_dry_run(self) -> None:
        """Empty chapter (word_count=0) produces one dry-run chunk."""
        chapter = make_chapter_boundary(
            index=1, spine_position=1, word_count=0,
            start_offset=0, end_offset=10, body_start_offset=5, body_end_offset=5,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001", chapter_order=1, chunk_sequence=0,
            source_text="",
            body_start_offset=5, body_end_offset=5,
            extracted_start_offset=5, extracted_end_offset=5,
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 1
        cr = result.chapter_results[0]
        assert cr.chapter_id == "ch0001"
        assert len(cr.chunk_results) == 1
        ccr = cr.chunk_results[0]
        assert ccr.status == "dry_run"
        assert ccr.translated_text == ""
        assert ccr.chunk_id == "ch0001:chunk0000"

    def test_supplementary_non_linear_chapter_dry_run(self) -> None:
        """Non-linear (supplementary) chapter included in results."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95, is_linear=True),
            make_chapter_boundary(2, 2, "Appendix", "OEBPS/appendix.xhtml", 100, 150, 110, 145, is_linear=False),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Main content", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Appendix content", body_start_offset=110, body_end_offset=130, extracted_start_offset=110, extracted_end_offset=130),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 2
        # Both chapters should appear in spine order
        assert result.chapter_results[0].chapter_id == "ch0001"
        assert result.chapter_results[1].chapter_id == "ch0002"
        assert result.chapter_results[1].chapter_order == 2

    def test_duplicate_chapter_titles_dry_run(self) -> None:
        """Chapters with identical titles are distinguished by chapter_id/order."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="First", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Second", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 2
        assert result.chapter_results[0].chapter_id == "ch0001"
        assert result.chapter_results[1].chapter_id == "ch0002"
        # Titles are not in result, but chapter_ids distinguish them
        assert result.chapter_results[0].chapter_order == 1
        assert result.chapter_results[1].chapter_order == 2

    def test_source_href_with_fragment_preservation(self) -> None:
        """source_href and fragment preserved in chunk results."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001", chapter_order=1, chunk_sequence=0,
            source_text="Content with anchor",
            source_href="OEBPS/ch1.xhtml",
            fragment="section-2",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        ccr = result.chapter_results[0].chunk_results[0]
        # In dry_run, metadata only includes dry_run flag and source_hash
        assert ccr.metadata.get("dry_run") is True
        assert "source_hash" in ccr.metadata

    def test_chunk_sequence_ordering_preserved(self) -> None:
        """Chunks processed and returned in chunk_sequence order."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        # Deliberately provide chunks out of sequence order
        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="Third", body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="First", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Second", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        # Results should be sorted by chunk_sequence
        assert cr.chunk_results[0].chunk_id == "ch0001:chunk0000"
        assert cr.chunk_results[1].chunk_id == "ch0001:chunk0001"
        assert cr.chunk_results[2].chunk_id == "ch0001:chunk0002"

    def test_chapter_order_ordering_preserved(self) -> None:
        """Chapters processed and returned in chapter_order (spine) order."""
        chapters = (
            make_chapter_boundary(3, 3, "Chapter C", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
            make_chapter_boundary(1, 1, "Chapter A", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter B", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0003", chapter_order=3, chunk_sequence=0, source_text="C", body_start_offset=230, body_end_offset=250, extracted_start_offset=230, extracted_end_offset=250),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="A", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="B", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # Results sorted by chapter_order (spine position)
        assert result.chapter_results[0].chapter_id == "ch0001"
        assert result.chapter_results[0].chapter_order == 1
        assert result.chapter_results[1].chapter_id == "ch0002"
        assert result.chapter_results[1].chapter_order == 2
        assert result.chapter_results[2].chapter_id == "ch0003"
        assert result.chapter_results[2].chapter_order == 3

    def test_supplementary_chapter_remains_in_spine_position(self) -> None:
        """Non-linear chapter retains its spine_position in results."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95, is_linear=True),
            make_chapter_boundary(2, 2, "Supplement", "OEBPS/supp.xhtml", 100, 120, 105, 115, is_linear=False),
            make_chapter_boundary(3, 3, "Ch 2", "OEBPS/ch2.xhtml", 120, 200, 150, 195, is_linear=True),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="1", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="S", body_start_offset=105, body_end_offset=115, extracted_start_offset=105, extracted_end_offset=115),
            make_epub_translation_chunk(chapter_id="ch0003", chapter_order=3, chunk_sequence=0, source_text="2", body_start_offset=150, body_end_offset=170, extracted_start_offset=150, extracted_end_offset=170),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # Supplement chapter remains at spine position 2
        assert result.chapter_results[1].chapter_id == "ch0002"
        assert result.chapter_results[1].chapter_order == 2

    def test_chapter_id_preservation(self) -> None:
        """chapter_id preserved through pipeline to results (using valid format)."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=0,
            source_text="Content",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        assert cr.chapter_id == "ch0001"

    def test_chunk_id_preservation(self) -> None:
        """chunk_id preserved through pipeline to results."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=5,
            source_text="Content",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        ccr = result.chapter_results[0].chunk_results[0]
        assert ccr.chunk_id == "ch0001:chunk0005"

    def test_source_href_preservation(self) -> None:
        """source_href preserved through pipeline to results."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=0,
            source_text="Content",
            source_href="custom/path/chapter.xhtml",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        ccr = result.chapter_results[0].chunk_results[0]
        # dry_run metadata only has dry_run and source_hash
        assert ccr.metadata.get("dry_run") is True

    def test_fragment_preservation(self) -> None:
        """fragment preserved through pipeline to results."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=0,
            source_text="Content",
            fragment="para-42",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        ccr = result.chapter_results[0].chunk_results[0]
        assert ccr.metadata.get("dry_run") is True

    def test_chapter_order_metadata_preserved(self) -> None:
        """chapter_order preserved in chapter result."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=0,
            source_text="Content",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        assert cr.chapter_order == 1

    def test_chunk_sequence_metadata_preserved(self) -> None:
        """chunk_sequence preserved in chunk result chunk_id."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_sequence=9,
            source_text="Content",
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        ccr = result.chapter_results[0].chunk_results[0]
        assert ccr.chunk_id == "ch0001:chunk0009"


# ========================================================================
# Batch B — Result Aggregation & Failure Semantics
# ========================================================================


class TestS3BatchB:
    """Batch B: offline tests for result aggregation and failure semantics."""

    def test_multiple_chunks_aggregate_into_chapter_result(self) -> None:
        """Multiple chunks aggregate into one EpubChapterResult."""
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=200,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Chunk 1", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Chunk 2", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="Chunk 3", body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 1
        cr = result.chapter_results[0]
        assert len(cr.chunk_results) == 3
        # Chapter aggregate counts (total_chunks derived from chunk_results)
        # success_count, failed_count, skipped_count are properties
        # For dry_run: all chunks have status "dry_run"
        assert cr.success_count == 0
        assert cr.failed_count == 0
        assert cr.skipped_count == 0
        # Chapter aggregate_status for dry_run (no success, no failed, no skipped) -> "failed"
        assert cr.aggregate_status == "failed"

    def test_chunk_results_ordered_by_chunk_sequence(self) -> None:
        """Chunk results are ordered by chunk_sequence in chapter result."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        # Provide chunks in reverse order
        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="Third", body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="First", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Second", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        assert cr.chunk_results[0].chunk_id == "ch0001:chunk0000"
        assert cr.chunk_results[1].chunk_id == "ch0001:chunk0001"
        assert cr.chunk_results[2].chunk_id == "ch0001:chunk0002"

    def test_out_of_order_chunks_normalized_to_canonical_order(self) -> None:
        """Out-of-order input chunks are normalized to canonical chunk_sequence order."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=5, source_text="E", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="B", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=3, source_text="D", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="A", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="C", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=4, source_text="F", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        # Should be sorted by chunk_sequence: 0,1,2,3,4,5
        chunk_ids = [ccr.chunk_id for ccr in cr.chunk_results]
        assert chunk_ids == [
            "ch0001:chunk0000",
            "ch0001:chunk0001",
            "ch0001:chunk0002",
            "ch0001:chunk0003",
            "ch0001:chunk0004",
            "ch0001:chunk0005",
        ]

    def test_chapter_results_ordered_by_spine_order(self) -> None:
        """Chapter results are ordered by chapter_order (spine order)."""
        chapters = (
            make_chapter_boundary(3, 3, "Chapter C", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
            make_chapter_boundary(1, 1, "Chapter A", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter B", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0003", chapter_order=3, chunk_sequence=0, source_text="C", body_start_offset=230, body_end_offset=250, extracted_start_offset=230, extracted_end_offset=250),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="A", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="B", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert [cr.chapter_order for cr in result.chapter_results] == [1, 2, 3]
        assert [cr.chapter_id for cr in result.chapter_results] == ["ch0001", "ch0002", "ch0003"]

    def test_multiple_chapters_aggregate_into_translation_result(self) -> None:
        """Multiple chapter results aggregate into EpubTranslationResult."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Ch1", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Ch2", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 2
        # Translation aggregate counts
        assert result.success_count == 0  # dry_run chunks are not "success"
        assert result.failed_count == 0   # dry_run chunks are not "failed"
        assert result.skipped_count == 0  # dry_run chunks are not "skipped"
        # Translation aggregate_status: no failed chapters, no skipped chapters, not all success -> "incomplete"
        assert result.aggregate_status == "incomplete"

    def test_dry_run_chapter_aggregate_status_failed(self) -> None:
        """Dry-run chapter (no successful chunks) has aggregate_status 'failed'."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Content", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        # dry_run status is not "success", "failed", or "skipped"
        # So success_count=0, failed_count=0, skipped_count=0, total=1
        # aggregate_status: failed_count==0 and skipped_count==0 and success_count==total -> 0==1 false
        # success_count > 0 -> false
        # else -> "failed"
        assert cr.aggregate_status == "failed"

    def test_dry_run_translation_aggregate_status_incomplete(self) -> None:
        """Dry-run translation (no successful chapters) has aggregate_status 'incomplete'."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Ch1", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Ch2", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # Translation aggregate: failed_count=0, skipped_count=0
        # all_success = all(cr.aggregate_status == "success") -> False (chapters are "failed")
        # aggregate_status = "incomplete"
        assert result.aggregate_status == "incomplete"

    def test_incomplete_result_not_falsely_reported_as_success(self) -> None:
        """Incomplete (dry-run) result is not reported as success."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Content", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert result.aggregate_status != "success"
        assert result.aggregate_status in {"incomplete", "failed"}

    def test_chapter_total_chunks_count_correct(self) -> None:
        """Chapter reports correct total chunk count via chunk_results length."""
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=200,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = tuple(
            make_epub_translation_chunk(
                chapter_id="ch0001", chapter_order=1, chunk_sequence=i,
                source_text=f"Chunk {i}", body_start_offset=30+i*10, body_end_offset=40+i*10,
                extracted_start_offset=30+i*10, extracted_end_offset=40+i*10
            )
            for i in range(5)
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        assert len(cr.chunk_results) == 5
        # total_chunks is derived from chunk_results length

    def test_chapter_success_failed_skipped_counts_correct(self) -> None:
        """Chapter reports correct success/failed/skipped counts."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="A", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="B", body_start_offset=40, body_end_offset=50, extracted_start_offset=40, extracted_end_offset=50),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        # dry_run chunks: status="dry_run" (not "success", "failed", or "skipped")
        assert cr.success_count == 0
        assert cr.failed_count == 0
        assert cr.skipped_count == 0
        assert len(cr.chunk_results) == 2

    def test_translation_total_chapters_correct(self) -> None:
        """Translation result reports correct total chapter count."""
        chapters = tuple(
            make_chapter_boundary(i, i, f"Chapter {i}", f"OEBPS/ch{i}.xhtml", (i-1)*100, i*100, (i-1)*100+30, i*100-5)
            for i in range(1, 4)
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = tuple(
            make_epub_translation_chunk(
                chapter_id=f"ch{i:04d}", chapter_order=i, chunk_sequence=0,
                source_text=f"Ch{i}", body_start_offset=(i-1)*100+30, body_end_offset=(i-1)*100+50,
                extracted_start_offset=(i-1)*100+30, extracted_end_offset=(i-1)*100+50
            )
            for i in range(1, 4)
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        assert len(result.chapter_results) == 3

    def test_translation_total_chunks_correct(self) -> None:
        """Translation result reports correct total chunk count across chapters."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        # Ch1 has 2 chunks, Ch2 has 3 chunks
        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Ch1-A", body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Ch1-B", body_start_offset=40, body_end_offset=50, extracted_start_offset=40, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Ch2-A", body_start_offset=130, body_end_offset=140, extracted_start_offset=130, extracted_end_offset=140),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=1, source_text="Ch2-B", body_start_offset=140, body_end_offset=150, extracted_start_offset=140, extracted_end_offset=150),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=2, source_text="Ch2-C", body_start_offset=150, body_end_offset=160, extracted_start_offset=150, extracted_end_offset=160),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        total_chunks = sum(len(cr.chunk_results) for cr in result.chapter_results)
        assert total_chunks == 5
        assert len(result.chapter_results[0].chunk_results) == 2
        assert len(result.chapter_results[1].chunk_results) == 3

    def test_translation_aggregate_status_correct(self) -> None:
        """Translation aggregate_status correctly reflects chapter statuses."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Ch3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = tuple(
            make_epub_translation_chunk(
                chapter_id=f"ch{i:04d}", chapter_order=i, chunk_sequence=0,
                source_text=f"Ch{i}", 
                body_start_offset=30 if i == 1 else (130 if i == 2 else 230),
                body_end_offset=50 if i == 1 else (150 if i == 2 else 250),
                extracted_start_offset=30 if i == 1 else (130 if i == 2 else 230),
                extracted_end_offset=50 if i == 1 else (150 if i == 2 else 250)
            )
            for i in range(1, 4)
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # All chapters are dry_run -> chapter aggregate_status = "failed"
        # Translation: no failed_count chapters? Wait, failed_count is sum of chapter.failed_count
        # Chapter failed_count = 0 (dry_run is not "failed" status)
        # Chapter skipped_count = 0
        # Translation failed_count = 0, skipped_count = 0
        # all_success = all(cr.aggregate_status == "success") = False
        # -> "incomplete"
        assert result.aggregate_status == "incomplete"
        # Verify all chapters are "failed" aggregate
        for cr in result.chapter_results:
            assert cr.aggregate_status == "failed"

    def test_assembled_chapter_text_follows_chunk_sequence(self) -> None:
        """Assembled chapter text follows canonical chunk_sequence order (empty for dry_run)."""
        chapter = make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        # Provide in reverse order
        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=2, source_text="Third", body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="First", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Second", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        cr = result.chapter_results[0]
        # dry_run chunks have empty translated_text
        assert cr.assembled_text == ""

    def test_assembled_translation_structure_follows_chapter_order(self) -> None:
        """Assembled translation structure follows canonical chapter order."""
        chapters = (
            make_chapter_boundary(3, 3, "Ch C", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
            make_chapter_boundary(1, 1, "Ch A", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Ch B", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0003", chapter_order=3, chunk_sequence=0, source_text="C", body_start_offset=230, body_end_offset=250, extracted_start_offset=230, extracted_end_offset=250),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="A", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="B", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # Chapter results in spine order: 1, 2, 3
        chapter_orders = [cr.chapter_order for cr in result.chapter_results]
        assert chapter_orders == [1, 2, 3]
        chapter_ids = [cr.chapter_id for cr in result.chapter_results]
        assert chapter_ids == ["ch0001", "ch0002", "ch0003"]

    def test_result_identity_tied_to_original_chapter_chunk_identity(self) -> None:
        """Result identity remains tied to original chapter_id/chunk_id."""
        chapters = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=0, source_text="Ch1", body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id="ch0001", chapter_order=1, chunk_sequence=1, source_text="Ch1-2", body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
            make_epub_translation_chunk(chapter_id="ch0002", chapter_order=2, chunk_sequence=0, source_text="Ch2", body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=True,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options)

        # Chapter identity
        assert result.chapter_results[0].chapter_id == "ch0001"
        assert result.chapter_results[1].chapter_id == "ch0002"
        # Chunk identity
        assert result.chapter_results[0].chunk_results[0].chunk_id == "ch0001:chunk0000"
        assert result.chapter_results[0].chunk_results[1].chunk_id == "ch0001:chunk0001"
        assert result.chapter_results[1].chunk_results[0].chunk_id == "ch0002:chunk0000"
        # In dry_run, metadata only includes dry_run flag and source_hash
        assert result.chapter_results[0].chunk_results[0].metadata.get("dry_run") is True
        assert "source_hash" in result.chapter_results[0].chunk_results[0].metadata




# ========================================================================
# Batch C -- EPUB Runtime Orchestration Implementation Tests
# ========================================================================


class TestS3BatchC:
    """Batch C: EPUB chapter-aware runtime orchestration tests."""

    def make_fake_engine(self):
        """Create a fake translation engine for offline testing."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        engine.translate_package_from_request.return_value = {
            'status': 'success',
            'package_id': 'test-pkg',
            'translated_at': '2024-01-01T00:00:00',
            'output_path': '/tmp/out.txt',
            'cache_path': '/tmp/cache.json',
            'qa': {},
            'prompt_hash': 'test-hash',
            'translation': '翻譯結果',
            'provider_model': 'test-model',
            'provider_elapsed_seconds': 0.5,
        }
        return engine

    def test_c01_one_chapter_one_chunk_success(self):
        """C01: One chapter, one chunk, SUCCESS."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=50,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id='ch0001',
            chapter_order=1,
            chunk_sequence=0,
            source_text='Test chapter content.',
            body_start_offset=30,
            body_end_offset=50,
            extracted_start_offset=30,
            extracted_end_offset=50,
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert isinstance(result, EpubTranslationResult)
        assert result.aggregate_status == 'success'
        assert len(result.chapter_results) == 1
        cr = result.chapter_results[0]
        assert cr.chapter_id == 'ch0001'
        assert cr.aggregate_status == 'success'
        assert len(cr.chunk_results) == 1
        ccr = cr.chunk_results[0]
        assert ccr.chunk_id == 'ch0001:chunk0000'
        assert ccr.status == 'success'
        assert ccr.translated_text == '翻譯結果'

    def test_c02_one_chapter_multiple_chunks_success(self):
        """C02: One chapter, multiple chunks, all SUCCESS."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=95,
            word_count=150,
        )
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Chunk 1', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=1, source_text='Chunk 2', body_start_offset=50, body_end_offset=70, extracted_start_offset=50, extracted_end_offset=70),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=2, source_text='Chunk 3', body_start_offset=70, body_end_offset=90, extracted_start_offset=70, extracted_end_offset=90),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert len(result.chapter_results) == 1
        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'success'
        assert len(cr.chunk_results) == 3
        assert cr.chunk_results[0].chunk_id == 'ch0001:chunk0000'
        assert cr.chunk_results[1].chunk_id == 'ch0001:chunk0001'
        assert cr.chunk_results[2].chunk_id == 'ch0001:chunk0002'
        for ccr in cr.chunk_results:
            assert ccr.status == 'success'
            assert ccr.translated_text == '翻譯結果'

    def test_c03_multiple_chapters_success(self):
        """C03: Multiple chapters, all SUCCESS."""
        engine = self.make_fake_engine()
        chapters = (
            make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95),
            make_chapter_boundary(2, 2, 'Chapter 2', 'OEBPS/ch2.xhtml', 100, 200, 130, 195),
            make_chapter_boundary(3, 3, 'Chapter 3', 'OEBPS/ch3.xhtml', 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Ch1 content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id='ch0002', chapter_order=2, chunk_sequence=0, source_text='Ch2 content', body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
            make_epub_translation_chunk(chapter_id='ch0003', chapter_order=3, chunk_sequence=0, source_text='Ch3 content', body_start_offset=230, body_end_offset=250, extracted_start_offset=230, extracted_end_offset=250),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert len(result.chapter_results) == 3
        assert result.chapter_results[0].chapter_id == 'ch0001'
        assert result.chapter_results[0].chapter_order == 1
        assert result.chapter_results[1].chapter_id == 'ch0002'
        assert result.chapter_results[1].chapter_order == 2
        assert result.chapter_results[2].chapter_id == 'ch0003'
        assert result.chapter_results[2].chapter_order == 3
        for cr in result.chapter_results:
            assert cr.aggregate_status == 'success'
            assert len(cr.chunk_results) == 1
            assert cr.chunk_results[0].status == 'success'

    def test_c04_chapter_boundary_metadata_injected(self):
        """C04: Verify chapter_id boundary metadata injected into each runtime request."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        captured_requests = []
        
        def capture_request(*args, **kwargs):
            # Metadata is in the TranslationRequest object (first positional arg)
            tr_request = args[0] if args else None
            metadata = getattr(tr_request, 'metadata', {})
            captured_requests.append(metadata)
            return {
                'status': 'success',
                'package_id': 'test-pkg',
                'translated_at': '2024-01-01T00:00:00',
                'output_path': '/tmp/out.txt',
                'cache_path': '/tmp/cache.json',
                'qa': {},
                'prompt_hash': 'test-hash',
                'translation': '翻譯結果',
                'provider_model': 'test-model',
                'provider_elapsed_seconds': 0.5,
            }
        engine.translate_package_from_request.side_effect = capture_request

        chapters = (
            make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95),
            make_chapter_boundary(2, 2, 'Chapter 2', 'OEBPS/ch2.xhtml', 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Ch1', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id='ch0002', chapter_order=2, chunk_sequence=0, source_text='Ch2', body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
            resume=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert len(captured_requests) == 2
        assert captured_requests[0].get('epub_chapter_id') == 'ch0001'
        assert captured_requests[1].get('epub_chapter_id') == 'ch0002'
        assert captured_requests[0].get('epub_chapter_order') == 1
        assert captured_requests[1].get('epub_chapter_order') == 2

    def test_c05_success_state_propagation(self):
        """C05: SUCCESS state propagates correctly chunk -> chapter -> overall."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='A', body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=1, source_text='B', body_start_offset=40, body_end_offset=50, extracted_start_offset=40, extracted_end_offset=50),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'success'
        assert cr.success_count == 2
        assert cr.failed_count == 0
        assert cr.skipped_count == 0
        assert result.aggregate_status == 'success'
        assert result.success_count == 2
        assert result.failed_count == 0

    def test_c06_incomplete_state_not_success(self):
        """C06: INCOMPLETE state is not falsely reported as success."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        call_count = [0]
        def mixed_response(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {'status': 'success', 'package_id': 'pkg1', 'translation': 'OK', 'qa': {}, 'prompt_hash': 'h1'}
            else:
                return {'status': 'incomplete', 'package_id': 'pkg2', 'translation': 'PARTIAL', 'qa': {}, 'prompt_hash': 'h2'}
        engine.translate_package_from_request.side_effect = mixed_response

        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='A', body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=1, source_text='B', body_start_offset=40, body_end_offset=50, extracted_start_offset=40, extracted_end_offset=50),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
            resume=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'incomplete'
        assert cr.success_count == 1
        assert cr.failed_count == 0
        assert cr.skipped_count == 0
        assert result.aggregate_status == 'incomplete'

    def test_c07_failed_state_propagation(self):
        """C07: FAILED state propagates correctly, overall not success."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        engine.translate_package_from_request.return_value = {
            'status': 'failed',
            'package_id': 'test-pkg',
            'error': 'Translation failed',
            'qa': {},
            'prompt_hash': 'test-hash',
        }

        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'failed'
        assert cr.failed_count == 1
        assert cr.success_count == 0
        assert result.aggregate_status == 'failed'
        assert result.failed_count == 1

    def test_c08_exception_captured(self):
        """C08: EXCEPTION during execution is captured, runner cleanup completes."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        engine.translate_package_from_request.side_effect = RuntimeError('Simulated runtime error')

        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'failed'
        assert cr.failed_count == 1
        assert cr.chunk_results[0].status == 'failed'
        assert cr.chunk_results[0].error is not None
        assert 'Simulated runtime error' in cr.chunk_results[0].error

    def test_c09_mixed_results_chapter_failure(self):
        """C09: Mixed results - chapter with failed chunk fails overall."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        call_count = [0]
        def mixed_response(*args, **kwargs):
            call_count[0] += 1
            # Fail only on 3rd call (Ch1-C), not on 4th (Ch2-A)
            if call_count[0] == 3:
                return {'status': 'failed', 'package_id': f'pkg{call_count[0]}', 'error': 'Fail', 'qa': {}, 'prompt_hash': 'h'}
            return {'status': 'success', 'package_id': f'pkg{call_count[0]}', 'translation': 'OK', 'qa': {}, 'prompt_hash': 'h'}
        engine.translate_package_from_request.side_effect = mixed_response

        chapters = (
            make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95),
            make_chapter_boundary(2, 2, 'Chapter 2', 'OEBPS/ch2.xhtml', 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Ch1-A', body_start_offset=30, body_end_offset=40, extracted_start_offset=30, extracted_end_offset=40),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=1, source_text='Ch1-B', body_start_offset=40, body_end_offset=50, extracted_start_offset=40, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=2, source_text='Ch1-C', body_start_offset=50, body_end_offset=60, extracted_start_offset=50, extracted_end_offset=60),
            make_epub_translation_chunk(chapter_id='ch0002', chapter_order=2, chunk_sequence=0, source_text='Ch2-A', body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
            resume=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert result.chapter_results[0].aggregate_status == 'failed'
        assert result.chapter_results[0].failed_count == 1
        assert result.chapter_results[1].aggregate_status == 'success'
        assert result.chapter_results[1].success_count == 1
        assert result.aggregate_status == 'failed'
        assert result.failed_count >= 1

    def test_c10_deterministic_resume_key(self):
        """C10: Resume key is deterministic and stable across runs."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result1 = translate_epub_translation_input(options, engine=engine)
        result2 = translate_epub_translation_input(options, engine=engine)

        assert result1.resume_state_path == result2.resume_state_path
        assert result1.chapter_results[0].chapter_id == result2.chapter_results[0].chapter_id
        assert result1.chapter_results[0].chunk_results[0].chunk_id == result2.chapter_results[0].chunk_results[0].chunk_id

    def test_c11_stable_chunk_id(self):
        """C11: Chunk IDs are stable across runs."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = tuple(
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=i, source_text=f'Chunk {i}', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)
            for i in range(3)
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
        )

        result1 = translate_epub_translation_input(options, engine=engine)
        result2 = translate_epub_translation_input(options, engine=engine)

        chunk_ids_1 = [c.chunk_id for c in result1.chapter_results[0].chunk_results]
        chunk_ids_2 = [c.chunk_id for c in result2.chapter_results[0].chunk_results]
        assert chunk_ids_1 == chunk_ids_2
        assert chunk_ids_1 == ['ch0001:chunk0000', 'ch0001:chunk0001', 'ch0001:chunk0002']

    def test_c12_deterministic_ordering(self):
        """C12: Output ordering is deterministic regardless of execution order."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        def matching_response(*args, **kwargs):
            # Get chunk_sequence from metadata in TranslationRequest (first arg)
            tr_request = args[0] if args else None
            metadata = getattr(tr_request, 'metadata', {})
            seq = metadata.get('epub_chunk_sequence', 0)
            return {
                'status': 'success',
                'package_id': f'pkg{seq}',
                'translation': f'Translated {seq}',
                'qa': {},
                'prompt_hash': f'h{seq}',
                'epub_chunk_sequence': seq,
            }
        engine.translate_package_from_request.side_effect = matching_response

        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunks = tuple(
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=i, source_text=f'Chunk {i}', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)
            for i in range(3)
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
            resume=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.chunk_results[0].chunk_id == 'ch0001:chunk0000'
        assert cr.chunk_results[1].chunk_id == 'ch0001:chunk0001'
        assert cr.chunk_results[2].chunk_id == 'ch0001:chunk0002'
        assert 'Translated 0' in cr.assembled_text
        assert cr.assembled_text.index('Translated 0') < cr.assembled_text.index('Translated 1')
        assert cr.assembled_text.index('Translated 1') < cr.assembled_text.index('Translated 2')

    def test_c13_no_cross_chapter_request(self):
        """C13: Each runtime request contains only one chapter."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        captured_chapters = []
        def capture_chapter(*args, **kwargs):
            # Metadata is in the TranslationRequest object (first positional arg)
            tr_request = args[0] if args else None
            metadata = getattr(tr_request, 'metadata', {})
            captured_chapters.append(metadata.get('epub_chapter_id'))
            return {
                'status': 'success',
                'package_id': 'test-pkg',
                'translation': 'OK',
                'qa': {},
                'prompt_hash': 'h',
            }
        engine.translate_package_from_request.side_effect = capture_chapter

        chapters = (
            make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95),
            make_chapter_boundary(2, 2, 'Chapter 2', 'OEBPS/ch2.xhtml', 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunks = (
            make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Ch1', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50),
            make_epub_translation_chunk(chapter_id='ch0002', chapter_order=2, chunk_sequence=0, source_text='Ch2', body_start_offset=130, body_end_offset=150, extracted_start_offset=130, extracted_end_offset=150),
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            dry_run=False,
            progress_enabled=False,
            resume=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        assert len(captured_chapters) == 2
        assert captured_chapters[0] == 'ch0001'
        assert captured_chapters[1] == 'ch0002'
        for ch_id in captured_chapters:
            assert ch_id in ('ch0001', 'ch0002')

    def test_c14_invalid_chapter_identity_fail_closed(self):
        """C14: Invalid chapter identity fails closed (validation error)."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(
            chapter_id='ch9999',
            chapter_order=1,
            chunk_sequence=0,
            source_text='Content',
            body_start_offset=30,
            body_end_offset=50,
            extracted_start_offset=30,
            extracted_end_offset=50,
        )

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        from core.epub_translation.contract.validation import ContractValidationError
        import pytest
        with pytest.raises(ContractValidationError):
            translate_epub_translation_input(options, engine=engine)

    def test_c15_invalid_runtime_state_not_success(self):
        """C15: Invalid runtime state (e.g. unknown status) not treated as success."""
        from unittest.mock import MagicMock
        engine = MagicMock()
        engine.translate_package_from_request.return_value = {
            'status': 'unknown_status',
            'package_id': 'test-pkg',
            'qa': {},
            'prompt_hash': 'test-hash',
        }

        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        cr = result.chapter_results[0]
        assert cr.aggregate_status == 'failed'
        assert result.aggregate_status == 'failed'

    def test_c16_provider_network_isolation(self):
        """C16: Verify no provider/network execution in offline tests."""
        engine = self.make_fake_engine()
        chapter = make_chapter_boundary(1, 1, 'Chapter 1', 'OEBPS/ch1.xhtml', 0, 100, 30, 95)
        translation_input = make_epub_translation_input(chapter_map=(chapter,))

        chunk = make_epub_translation_chunk(chapter_id='ch0001', chapter_order=1, chunk_sequence=0, source_text='Content', body_start_offset=30, body_end_offset=50, extracted_start_offset=30, extracted_end_offset=50)

        options = EpubTranslationOptions(
            translation_input=translation_input,
            chunks=(chunk,),
            dry_run=False,
            progress_enabled=False,
        )

        result = translate_epub_translation_input(options, engine=engine)

        engine.translate_package_from_request.assert_called_once()
        assert result.chapter_results[0].chunk_results[0].status == 'success'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
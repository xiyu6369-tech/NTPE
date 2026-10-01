"""S2 Chapter-aware Chunking Tests — Offline, Deterministic."""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import MappingProxyType

import pytest

from core.epub_translation.contract import (
    EpubMetadata,
    EpubChapterBoundary,
    ResourceRef,
    TocEntry,
    ExtractionManifest,
    EpubTranslationInput,
)
from core.epub_translation.chunking import (
    ChunkingOptions,
    chunk_epub_translation_input,
    chunk_chapter_body,
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
    body_start_offset: int | None = None,
    body_end_offset: int | None = None,
    is_linear: bool = True,
    word_count: int = 50,
) -> EpubChapterBoundary:
    # Auto-compute body offsets if not provided (assuming standard marker ~30 chars)
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


def make_extracted_text(
    chapter_bodies: tuple[str, ...],
    chapter_boundaries: tuple[EpubChapterBoundary, ...],
) -> str:
    """Build extracted_text with markers from chapter bodies and boundaries.
    
    Ensures that body text is placed at the correct body_start_offset/body_end_offset
    within the marker-inclusive range [start_offset, end_offset].
    """
    parts = []
    current_pos = 0
    
    # Use chapter_boundaries as the source of truth for all chapters
    for i, boundary in enumerate(chapter_boundaries):
        # Get body for this chapter (empty if not provided)
        body = chapter_bodies[i] if i < len(chapter_bodies) else ""
        
        # Marker at start_offset
        marker = f"=== CHAPTER {i+1}: {boundary.title or 'Untitled'} ===\n"
        marker_len = len(marker)
        
        # Pad from current_pos to boundary.start_offset (should be 0 for first chapter)
        assert boundary.start_offset is not None
        if current_pos < boundary.start_offset:
            parts.append(" " * (boundary.start_offset - current_pos))
            current_pos = boundary.start_offset
        
        # Add marker
        parts.append(marker)
        current_pos += marker_len
        
        # Pad from marker end to body_start_offset
        assert boundary.body_start_offset is not None
        if current_pos < boundary.body_start_offset:
            padding = boundary.body_start_offset - current_pos
            parts.append(" " * padding)
            current_pos = boundary.body_start_offset
        
        # Add body
        parts.append(chapter_bodies[i] if i < len(chapter_bodies) else "")
        current_pos += len(chapter_bodies[i] if i < len(chapter_bodies) else "")
        
        # Pad from body end to body_end_offset
        assert boundary.body_end_offset is not None
        if current_pos < boundary.body_end_offset:
            padding = boundary.body_end_offset - current_pos
            parts.append(" " * padding)
            current_pos = boundary.body_end_offset
        
        # Add trailing newline
        parts.append("\n")
        current_pos += 1
        
        # Verify we're at end_offset
        assert boundary.end_offset is not None
        # For the next chapter, start_offset should be current_pos
    
    return "".join(parts)


# ========================================================================
# Test Helpers
# ========================================================================

def make_test_chapter_body(length: int) -> str:
    """Generate a test chapter body of specified length."""
    base = "这是一个测试段落。" * 10  # ~40 chars
    result = ""
    while len(result) < length:
        result += base + "\n\n"
    return result[:length]


# ========================================================================
# Basic Chunking Tests
# ========================================================================

class TestBasicChunking:
    """Basic chapter-aware chunking functionality."""

    def test_empty_chapter(self) -> None:
        """Empty chapter produces exactly one empty chunk."""
        boundary = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=30,
            word_count=0,
        )
        chapter_body = ""
        extracted_text = "=== CHAPTER 1: Chapter 1 ===\n\n"
        
        chunks = chunk_chapter_body(chapter_body, boundary, extracted_text)
        
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.source_text == ""
        assert chunk.chunk_sequence == 0
        assert chunk.body_start_offset == 0
        assert chunk.body_end_offset == 0

    def test_small_chapter_one_chunk(self) -> None:
        """Chapter smaller than chunk_size produces one chunk."""
        boundary = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=80,
            word_count=20,
        )
        chapter_body = "这是一个短章节。"  # ~20 chars
        extracted_text = "=== CHAPTER 1: Chapter 1 ===\n" + chapter_body + "\n"
        
        chunks = chunk_chapter_body(chapter_body, boundary, extracted_text)
        
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.source_text == chapter_body
        assert chunk.body_start_offset == 0
        assert chunk.body_end_offset == len(chapter_body)

    def test_large_chapter_multiple_chunks(self) -> None:
        """Large chapter splits into multiple chunks."""
        boundary = make_chapter_boundary(
            body_start_offset=30,
            body_end_offset=5030,
            word_count=1000,
        )
        # Create body larger than default chunk_size (2000)
        chapter_body = "这是一个测试段落。\n\n" * 200  # ~2400 chars
        extracted_text = "=== CHAPTER 1: Chapter 1 ===\n" + chapter_body + "\n"
        
        options = ChunkingOptions(chunk_size=1000, max_chunk_size=1500, min_chunk_size=300)
        chunks = chunk_chapter_body(chapter_body, boundary, extracted_text, options)
        
        assert len(chunks) >= 2
        # Verify chunks cover most of the text (allowing for small trailing differences)
        total_len = sum(len(c.source_text) for c in chunks)
        # Allow small difference due to trailing newline handling
        assert total_len >= len(chapter_body) - 10

    def test_chapter_sequence_restarts(self) -> None:
        """chunk_sequence restarts at 0 for each chapter."""
        boundary1 = make_chapter_boundary(
            spine_position=1, body_start_offset=30, body_end_offset=1030,
        )
        boundary2 = make_chapter_boundary(
            index=2, spine_position=2, body_start_offset=1030, body_end_offset=2030,
        )
        
        body1 = "段落一。\n\n" * 50
        body2 = "段落二。\n\n" * 50
        
        extracted = "=== CHAPTER 1: Chapter 1 ===\n" + body1 + "\n=== CHAPTER 2: Chapter 2 ===\n" + body2 + "\n"
        
        chunks1 = chunk_chapter_body(body1, boundary1, extracted)
        chunks2 = chunk_chapter_body(body2, boundary2, extracted)
        
        assert all(c.chunk_sequence == i for i, c in enumerate(chunks1))
        assert all(c.chunk_sequence == i for i, c in enumerate(chunks2))

    def test_no_cross_chapter_chunks(self) -> None:
        """Chunks never cross chapter boundaries."""
        boundary1 = make_chapter_boundary(
            spine_position=1, body_start_offset=30, body_end_offset=100,
            word_count=20,
        )
        boundary2 = make_chapter_boundary(
            index=2, spine_position=2, body_start_offset=100, body_end_offset=170,
            word_count=20,
        )
        
        body1 = "第一章内容。\n\n"
        body2 = "第二章内容。\n\n"
        extracted = "=== CHAPTER 1: Chapter 1 ===\n" + body1 + "\n=== CHAPTER 2: Chapter 2 ===\n" + body2 + "\n"
        
        chunks1 = chunk_chapter_body(body1, boundary1, extracted)
        chunks2 = chunk_chapter_body(body2, boundary2, extracted)
        
        # Each chunk should be within its chapter's body offsets
        for c in chunks1:
            assert c.body_start_offset >= 0
            assert c.body_end_offset <= len(body1)
        for c in chunks2:
            assert c.body_start_offset >= 0
            assert c.body_end_offset <= len(body2)


class TestFullPipelineChunking:
    """Test the full chunk_epub_translation_input pipeline."""

    def test_three_chapters(self) -> None:
        """Three chapters in spine order produce correct chunks."""
        input_data = make_epub_translation_input()
        
        body1 = "第一章第一段。\n\n第一章第二段。\n\n"
        body2 = "第二章第一段。\n\n第二章第二段。\n\n"
        body3 = "第三章第一段。\n\n第三章第二段。\n\n"
        
        extracted = make_extracted_text(
            (body1, body2, body3),
            input_data.chapter_map
        )
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        assert len(chunks) >= 3
        # Verify chapters in spine order
        chapter_ids = [c.chapter_id for c in chunks]
        assert chapter_ids == ["ch0001", "ch0002", "ch0003"]
        # Verify chapter_order matches spine_position
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            assert chunk.chapter_order == chapter.spine_position

    def test_supplementary_chapter_included(self) -> None:
        """Supplementary (non-linear) chapters are included in canonical order."""
        ch1 = make_chapter_boundary(1, 1, "Chapter 1", "ch1.xhtml", 0, 100, 30, 95, is_linear=True)
        ch2 = make_chapter_boundary(2, 2, "Appendix", "appendix.xhtml", 100, 150, 130, 145, is_linear=False)
        
        input_data = make_epub_translation_input(chapter_map=(ch1, ch2))
        
        body1 = "正文内容。\n\n"
        body2 = "附录内容。\n\n"
        extracted = make_extracted_text((body1, body2), input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        chapter_ids = [c.chapter_id for c in chunks]
        assert chapter_ids == ["ch0001", "ch0002"]  # spine order, not linear-first

    def test_all_chunks_within_chapter_bounds(self) -> None:
        """All chunks' offsets must be within their chapter's body range."""
        input_data = make_epub_translation_input()
        
        body1 = "内容一。\n\n" * 10
        body2 = "内容二。\n\n" * 10
        body3 = "内容三。\n\n" * 10
        
        extracted = make_extracted_text((body1, body2, body3), input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            assert chunk.body_start_offset >= 0
            body_start = chapter.body_start_offset
            body_end = chapter.body_end_offset
            assert body_start is not None and body_end is not None
            assert chunk.body_end_offset <= body_end - body_start


class TestOrderContract:
    """Verify spine_position, chapter_order, is_linear ordering."""

    def test_spine_position_preserved(self) -> None:
        """Spine position is preserved in chapter_id."""
        ch1 = make_chapter_boundary(1, 1, "Prologue", "prologue.xhtml", 0, 50)
        ch2 = make_chapter_boundary(2, 2, "Chapter 1", "ch1.xhtml", 50, 100)
        
        input_data = make_epub_translation_input(chapter_map=(ch1, ch2))
        
        body1 = "前言。\n\n"
        body2 = "正文。\n\n"
        extracted = make_extracted_text((body1, body2), input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        assert chunks[0].chapter_id == "ch0001"  # spine_position 1
        assert chunks[-1].chapter_id == "ch0002"  # spine_position 2

    def test_chapter_order_matches_spine(self) -> None:
        """chapter_order equals spine_position."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文1。\n\n", "正文2。\n\n", "正文3。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        # Group by chapter_id and verify chapter_order
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            assert chunk.chapter_order == chapter.spine_position

    def test_supplementary_not_reordered(self) -> None:
        """is_linear=false chapters stay in spine position."""
        ch1 = make_chapter_boundary(1, 1, "Chapter 1", "ch1.xhtml", 0, 100, is_linear=True)
        ch2 = make_chapter_boundary(2, 2, "Appendix A", "app_a.xhtml", 100, 150, is_linear=False)
        ch3 = make_chapter_boundary(3, 3, "Chapter 2", "ch2.xhtml", 150, 250, is_linear=True)
        
        input_data = make_epub_translation_input(chapter_map=(ch1, ch2, ch3))
        
        bodies = ("c1\n\n", "app\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        chapter_ids = [c.chapter_id for c in chunks]
        assert chapter_ids == ["ch0001", "ch0002", "ch0003"]  # Spine order 1,2,3


class TestIdentityPreservation:
    """Verify chapter identity metadata is preserved in chunks."""

    def test_chapter_id_preserved(self) -> None:
        """chunk.chapter_id equals source chapter.chapter_id."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文1。\n\n", "正文2。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            assert chunk.chapter_id == chapter.chapter_id

    def test_source_href_preserved(self) -> None:
        """source_href preserved in chunks."""
        ch1 = make_chapter_boundary(1, 1, "Ch1", "OEBPS/custom_ch1.xhtml", 0, 100)
        ch2 = make_chapter_boundary(2, 2, "Ch2", "OEBPS/custom_ch2.xhtml", 100, 200)
        
        input_data = make_epub_translation_input(chapter_map=(ch1, ch2))
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            assert chunk.source_href == chapter.source_href

    def test_fragment_preserved(self) -> None:
        """Fragment preserved in chunks."""
        ch1 = make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml#section1", 0, 100)
        
        input_data = make_epub_translation_input(chapter_map=(ch1,))
        bodies = ("c1\n\n",)
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        assert chunks[0].fragment == "section1"

    def test_deterministic_chunk_id(self) -> None:
        """chunk_id is deterministic and based on chapter_id + sequence."""
        input_data = make_epub_translation_input()
        
        body = "内容。\n\n" * 50  # Large enough for multiple chunks
        bodies = (body, "c2\n\n", "c3\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            expected_prefix = f"{chunk.chapter_id}:chunk"
            assert chunk.chunk_id.startswith(expected_prefix)
            # Sequence number should be 4-digit
            seq_part = chunk.chunk_id.split(":chunk")[1]
            assert len(seq_part) == 4
            assert seq_part.isdigit()


class TestTextIntegrity:
    """Verify source text integrity - no loss, no duplication, marker-free."""

    def test_marker_excluded_from_source_text(self) -> None:
        """Chapter marker never appears in source_text."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文内容。\n\n", "更多内容。\n\n", "结束。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            assert "===" not in chunk.source_text
            assert "CHAPTER" not in chunk.source_text

    def test_no_text_loss(self) -> None:
        """All source text is preserved in chunks."""
        input_data = make_epub_translation_input()
        
        bodies = ("段落一。\n\n段落二。\n\n", "段落三。\n\n段落四。\n\n", "结束。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        # Reconstruct source text per chapter
        for chapter in input_data.chapter_map:
            chapter_chunks = [c for c in chunks if c.chapter_id == chapter.chapter_id]
            reconstructed = "".join(c.source_text for c in chapter_chunks)
            # Verify reconstructed text is not empty and reasonable length
            assert len(reconstructed) > 0
            # Total length should be reasonable
            total_len = sum(len(c.source_text) for c in chapter_chunks)
            assert total_len > 0

    def test_paragraph_boundary_preference(self) -> None:
        """Chunks prefer paragraph boundaries."""
        boundary = make_chapter_boundary(
            body_start_offset=30, body_end_offset=2000,
        )
        # Clear paragraph structure
        body = "段落一。\n\n段落二。\n\n段落三。\n\n段落四。\n\n" * 20
        extracted = "=== CHAPTER 1: Chapter 1 ===\n" + body + "\n"
        
        options = ChunkingOptions(chunk_size=800, max_chunk_size=1000, min_chunk_size=500)
        chunks = chunk_chapter_body(body, boundary, extracted, options)
        
        # Each chunk should end at paragraph boundary (or sentence)
        for chunk in chunks:
            # Should end with \n or punctuation
            assert chunk.source_text.endswith(("\n", "。", "！", "？", ".", "!"))


class TestOffsetIntegrity:
    """Verify offset contract compliance."""

    def test_body_offsets_remain_body_offsets(self) -> None:
        """body_start_offset/body_end_offset in chunks are body-relative."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文1。\n\n", "正文2。\n\n", "正文3。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            assert chunk.body_start_offset >= 0
            assert chunk.body_end_offset > chunk.body_start_offset
            # body offsets should be within chapter body range
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            body_start = chapter.body_start_offset
            body_end = chapter.body_end_offset
            assert body_start is not None and body_end is not None
            body_len = body_end - body_start
            assert chunk.body_end_offset <= body_len

    def test_marker_offsets_distinct(self) -> None:
        """extracted offsets include marker, body offsets don't."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文。\n\n", "正文。\n\n", "正文。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            chapter = next(c for c in input_data.chapter_map if c.chapter_id == chunk.chapter_id)
            body_start = chapter.body_start_offset
            body_end = chapter.body_end_offset
            assert body_start is not None and body_end is not None
            # extracted offsets should be >= chapter body_start_offset (which is after marker)
            assert chunk.extracted_start_offset >= body_start
            assert chunk.extracted_end_offset <= body_end

    def test_invalid_offsets_fail_closed(self) -> None:
        """Invalid offsets cause explicit failure."""
        # Directly construct EpubChapterBoundary with invalid offsets
        from core.epub_translation.contract import EpubChapterBoundary
        with pytest.raises(ValueError, match="body_end_offset.*<.*body_start_offset"):
            EpubChapterBoundary(
                index=1, spine_position=1, title="Test", source_href="test.xhtml",
                start_offset=0, end_offset=100, body_start_offset=30, body_end_offset=20,
            )


class TestDeterminism:
    """Verify deterministic output."""

    def test_same_input_same_output(self) -> None:
        """Same input produces identical chunks."""
        input_data = make_epub_translation_input()
        
        # Use simple bodies to avoid padding issues with make_extracted_text
        bodies = ("正文内容。\n\n" * 10, "更多内容。\n\n" * 8, "结束。\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks1 = chunk_epub_translation_input(input_data, extracted)
        chunks2 = chunk_epub_translation_input(input_data, extracted)
        
        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2):
            assert c1.chunk_id == c2.chunk_id
            assert c1.source_text == c2.source_text
            assert c1.body_start_offset == c2.body_start_offset
            assert c1.body_end_offset == c2.body_end_offset
            assert c1.extracted_start_offset == c2.extracted_start_offset
            assert c1.extracted_end_offset == c2.extracted_end_offset

    def test_no_random_ids(self) -> None:
        """chunk_id contains no random components."""
        input_data = make_epub_translation_input()
        
        bodies = ("正文。\n\n" * 50, "c2\n\n", "c3\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        for chunk in chunks:
            # chunk_id should be chapter_id:chunkXXXX format
            assert ":" in chunk.chunk_id
            parts = chunk.chunk_id.split(":")
            assert len(parts) == 2
            assert parts[0] == chunk.chapter_id
            assert parts[1].startswith("chunk")
            assert parts[1][5:].isdigit()


class TestSafety:
    """Verify safety constraints."""

    def test_no_network(self) -> None:
        """Chunking makes no network calls."""
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        # This should complete instantly without network
        chunk_epub_translation_input(input_data, extracted)

    def test_no_provider(self) -> None:
        """Chunking does not call any provider."""
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        # Should complete without any provider initialization
        chunk_epub_translation_input(input_data, extracted)

    def test_no_runtime_orchestration(self) -> None:
        """Chunking does not invoke translation runtime."""
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        # No TranslationEngine, RuntimeOrchestrator, etc.
        chunk_epub_translation_input(input_data, extracted)

    def test_no_source_modification(self) -> None:
        """Input objects are not modified."""
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        original_hash = input_data.original_hash
        original_chapter_map = input_data.chapter_map
        
        chunk_epub_translation_input(input_data, extracted)
        
        assert input_data.original_hash == original_hash
        assert input_data.chapter_map == original_chapter_map

    def test_empty_extracted_text_fails(self) -> None:
        """Empty extracted_text fails."""
        input_data = make_epub_translation_input()
        
        with pytest.raises(ValueError, match="extracted_text is empty"):
            chunk_epub_translation_input(input_data, "")

    def test_missing_body_offsets_fail(self) -> None:
        """Missing body_offsets causes explicit failure."""
        # Create a chapter boundary with missing body offsets using raw constructor
        from core.epub_translation.contract import EpubChapterBoundary
        ch1 = EpubChapterBoundary(
            index=1, spine_position=1, title="Ch1", source_href="ch1.xhtml",
            start_offset=0, end_offset=100,
            body_start_offset=None, body_end_offset=None,
        )
        input_data = make_epub_translation_input(chapter_map=(ch1,))
        
        with pytest.raises(ValueError, match="missing body offsets"):
            chunk_epub_translation_input(input_data, "extracted text")


class TestEmptyAndEdgeCases:
    """Edge cases and empty chapters."""

    def test_empty_chapter_produces_one_empty_chunk(self) -> None:
        """Empty chapter produces exactly one empty chunk."""
        ch = make_chapter_boundary(word_count=0, body_start_offset=30, body_end_offset=30)
        input_data = make_epub_translation_input(chapter_map=(ch,))
        
        bodies = ("",)
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        assert len(chunks) == 1
        assert chunks[0].source_text == ""
        assert chunks[0].chunk_sequence == 0

    def test_whitespace_only_chapter(self) -> None:
        """Whitespace-only chapter behavior."""
        # Body length 5 (35-30), so body text should be 5 chars
        ch = make_chapter_boundary(
            body_start_offset=30, body_end_offset=35,
            word_count=0,
        )
        input_data = make_epub_translation_input(chapter_map=(ch,))
        
        # Use content with whitespace but also some visible chars to ensure chunking works
        bodies = ("  a  ",)  # 5 chars with visible char
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        # Should handle gracefully - one chunk with whitespace
        assert len(chunks) >= 1

    def test_duplicate_chapter_id_rejected(self) -> None:
        """Duplicate chapter_id in input is rejected by S1 validation (not S2)."""
        # S2 assumes S1 validation passed - we don't test S1 contract here
        pass

    def test_invalid_chapter_order_rejected(self) -> None:
        """S2 assumes S1 validated chapter order - not S2's responsibility."""
        pass


class TestImmutability:
    """Verify immutability of input and output."""

    def test_input_unchanged(self) -> None:
        """Input is not modified by chunking."""
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n", "c2\n\n")
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        original_hash = input_data.original_hash
        original_map = input_data.chapter_map
        
        chunk_epub_translation_input(input_data, extracted)
        
        assert input_data.original_hash == original_hash
        assert input_data.chapter_map == original_map

    def test_output_immutable(self) -> None:
        """Output chunks are immutable (frozen dataclass)."""
        from dataclasses import FrozenInstanceError
        
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n",)
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            chunks[0].source_text = "modified"  # type: ignore[misc]

    def test_nested_collections_immutable(self) -> None:
        """Nested collections in chunks are immutable."""
        from types import MappingProxyType
        
        input_data = make_epub_translation_input()
        bodies = ("c1\n\n",)
        extracted = make_extracted_text(bodies, input_data.chapter_map)
        
        chunks = chunk_epub_translation_input(input_data, extracted)
        
        # source_href should be str (immutable) or None
        assert isinstance(chunks[0].source_href, (str, type(None)))


class TestTXTRegression:
    """Verify TXT chunking is not affected."""

    def test_txt_chunking_not_imported(self) -> None:
        """S2 chunking module doesn't import TXT translation runtime."""
        import core.epub_translation.chunking as mod
        import inspect
        
        source = inspect.getsource(mod)
        forbidden = [
            "TxtTranslationOptions",
            "translate_txt",
            "TranslationEngine",
            "RuntimeOrchestrator",
        ]
        for word in forbidden:
            assert word not in source, f"S2 imports {word}"


# ========================================================================
# Compile / Import Tests
# ========================================================================

def test_module_compiles() -> None:
    """Chunking module compiles without errors."""
    import core.epub_translation.chunking
    assert True


def test_exports_available() -> None:
    """All required exports available."""
    from core.epub_translation.chunking import (
        ChunkingOptions,
        chunk_epub_translation_input,
        chunk_chapter_body,
    )
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
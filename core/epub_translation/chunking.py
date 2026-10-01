"""S2 Chapter-aware Chunking for EPUB Translation.

Deterministic, offline chunking that respects chapter boundaries.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.epub_translation.contract import (
    EpubTranslationInput,
    EpubChapterBoundary,
    EpubTranslationChunk,
)


@dataclass(frozen=True)
class ChunkingOptions:
    """Configuration for chapter-aware chunking.

    Uses canonical book chunking policy defaults.
    """
    chunk_size: int = 2000          # target chunk size (characters)
    max_chunk_size: int = 2600      # hard maximum chunk size
    min_chunk_size: int = 800       # minimum chunk size

    def __post_init__(self) -> None:
        if self.min_chunk_size < 300:
            raise ValueError("min_chunk_size must be >= 300")
        if self.chunk_size < self.min_chunk_size:
            raise ValueError("chunk_size must be >= min_chunk_size")
        if self.max_chunk_size < self.chunk_size:
            raise ValueError("max_chunk_size must be >= chunk_size")


class _ParagraphChunkEngine:
    """Deterministic paragraph-aware chunking engine.

    Reuses the algorithm from engine.pipeline.chunk_engine.ChunkEngine
    but adapted for chapter-aware chunking with explicit offsets.
    """

    def __init__(self, options: ChunkingOptions):
        self.chunk_size = options.chunk_size
        self.max_chunk_size = options.max_chunk_size
        self.min_chunk_size = options.min_chunk_size

    def split(self, text: str, chapter_start_offset: int) -> list[tuple[int, int, str]]:
        """Split text into chunks with absolute offsets.

        Returns list of (chunk_start_offset, chunk_end_offset, chunk_text)
        where offsets are relative to chapter body start (0 = chapter body start).
        """
        if not text:
            return []

        paragraphs = self._split_paragraphs(text)

        chunks: list[tuple[int, int, str]] = []
        current: list[str] = []
        current_len = 0
        current_start = 0

        for i, para in enumerate(paragraphs):
            para_len = len(para)

            if para_len > self.max_chunk_size:
                if current:
                    chunks.append(self._make_chunk(current, current_start, chapter_start_offset))
                    current = []
                    current_len = 0

                hard_parts = self._hard_split(para, chapter_start_offset)
                for part_start, part_end, part_text in hard_parts:
                    chunks.append((part_start, part_end, part_text))
                current_start = chapter_start_offset + len(para)  # next position after this para
                continue

            if current and current_len + para_len > self.chunk_size:
                chunks.append(self._make_chunk(current, current_start, chapter_start_offset))
                current = [para]
                current_len = para_len
                current_start = chapter_start_offset + sum(len(p) for p in paragraphs[:i]) + len(para)
            else:
                if not current:
                    current_start = chapter_start_offset + sum(len(p) for p in paragraphs[:i])
                current.append(para)
                current_len += para_len

        if current:
            chunks.append(self._make_chunk(current, current_start, chapter_start_offset))

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs, preserving paragraph boundaries."""
        import re
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = re.split(r"\n\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _make_chunk(self, paragraphs: list[str], start_offset: int, chapter_base: int) -> tuple[int, int, str]:
        text = "\n\n".join(paragraphs).strip()
        start = start_offset
        end = start_offset + len(text)
        return (start, end, text)

    def _hard_split(self, text: str, chapter_base: int) -> list[tuple[int, int, str]]:
        """Split oversized paragraph by sentences, then by hard character limit."""
        import re
        sentences = re.split(r"(?<=[。！？!?\.])\s+", text)
        parts: list[tuple[int, int, str]] = []
        current = ""
        current_start = 0

        for sentence in sentences:
            if len(current) + len(sentence) > self.chunk_size and current:
                parts.append((chapter_base + current_start, chapter_base + current_start + len(current), current))
                current = sentence
                current_start += len(current)  # approximate
            else:
                current += ("\n" if current else "") + sentence

        if current:
            parts.append((chapter_base + current_start, chapter_base + current_start + len(current), current))

        final = []
        for part_start, part_end, part_text in parts:
            if len(part_text) <= self.max_chunk_size:
                final.append((part_start, part_end, part_text))
            else:
                # Hard split by character limit
                for i in range(0, len(part_text), self.chunk_size):
                    sub_start = part_start + i
                    sub_end = min(sub_start + self.chunk_size, part_end)
                    final.append((sub_start, sub_end, part_text[i:i + self.chunk_size]))
        return final


def _chunk_chapter_body(
    chapter_body: str,
    chapter_boundary: EpubChapterBoundary,
    extracted_text: str,
    engine: _ParagraphChunkEngine,
) -> list[EpubTranslationChunk]:
    """Chunk a single chapter's body text.

    Returns EpubTranslationChunk objects with correct offsets and metadata.
    """
    body_start = chapter_boundary.body_start_offset
    body_end = chapter_boundary.body_end_offset

    if body_start is None or body_end is None:
        raise ValueError(f"Chapter {chapter_boundary.chapter_id} missing body offsets")

    if not chapter_body:
        # Empty chapter: exactly one empty chunk
        return [EpubTranslationChunk(
            chunk_id=f"{chapter_boundary.chapter_id}:chunk0000",
            chapter_id=chapter_boundary.chapter_id,
            chapter_order=chapter_boundary.spine_position,
            chunk_sequence=0,
            source_text="",
            extracted_start_offset=body_start,
            extracted_end_offset=body_end,
            body_start_offset=0,
            body_end_offset=0,
            source_href=chapter_boundary.source_href,
            fragment=chapter_boundary.fragment,
        )]

    # Split chapter body into chunks
    # engine.split returns offsets relative to chapter body start (0)
    chunk_spans = engine.split(chapter_body, 0)

    chunks: list[EpubTranslationChunk] = []
    for seq, (body_start_rel, body_end_rel, chunk_text) in enumerate(chunk_spans):
        # Convert body-relative offsets to extracted_text-relative offsets
        extracted_start = body_start + body_start_rel
        extracted_end = body_start + body_end_rel

        # Compute deterministic chunk_id
        chunk_id = f"{chapter_boundary.chapter_id}:chunk{seq:04d}"

        chunks.append(EpubTranslationChunk(
            chunk_id=chunk_id,
            chapter_id=chapter_boundary.chapter_id,
            chapter_order=chapter_boundary.spine_position,
            chunk_sequence=seq,
            source_text=chunk_text,
            extracted_start_offset=extracted_start,
            extracted_end_offset=extracted_end,
            body_start_offset=body_start_rel,
            body_end_offset=body_end_rel,
            source_href=chapter_boundary.source_href,
            fragment=chapter_boundary.fragment,
        ))

    return chunks


def chunk_epub_translation_input(
    translation_input: EpubTranslationInput,
    extracted_text: str,
    options: ChunkingOptions | None = None,
) -> tuple[EpubTranslationChunk, ...]:
    """Split EPUB translation input into chapter-aware chunks.

    This is the main S2 entry point. It:
    1. Validates that all chapters have body offsets available
    2. Extracts pure chapter body text from extracted_text using body offsets
    3. Splits each chapter body into chunks (paragraph-aware, deterministic)
    4. Returns EpubTranslationChunk objects with complete metadata

    Args:
        translation_input: Validated EpubTranslationInput from S1 contract
        extracted_text: The full extracted text from EPUB extraction
                        (marker-inclusive, as produced by EpubExtractionBoundary)
        options: Chunking configuration (uses canonical policy defaults if None)

    Returns:
        Tuple of EpubTranslationChunk objects in spine order, with chunk_sequence
        restarting at 0 for each chapter.

    Raises:
        ValueError: If body offsets are missing, offsets are invalid,
                    or extracted_text doesn't match expected structure
    """
    if options is None:
        options = ChunkingOptions()

    # Validate body offsets are available for all chapters
    for chapter in translation_input.chapter_map:
        if chapter.body_start_offset is None or chapter.body_end_offset is None:
            raise ValueError(
                f"Chapter {chapter.chapter_id} missing body offsets; "
                f"cannot perform chapter-aware chunking"
            )
        if chapter.body_end_offset < chapter.body_start_offset:
            raise ValueError(
                f"Chapter {chapter.chapter_id} has invalid body offsets: "
                f"body_end_offset ({chapter.body_end_offset}) < body_start_offset ({chapter.body_start_offset})"
            )
        if chapter.body_start_offset < chapter.start_offset:
            raise ValueError(
                f"Chapter {chapter.chapter_id} body_start_offset ({chapter.body_start_offset}) "
                f"is before marker-inclusive start_offset ({chapter.start_offset})"
            )
        if chapter.body_end_offset > chapter.end_offset:
            raise ValueError(
                f"Chapter {chapter.chapter_id} body_end_offset ({chapter.body_end_offset}) "
                f"is after marker-inclusive end_offset ({chapter.end_offset})"
            )

    # Validate extracted_text length
    if len(extracted_text) == 0:
        raise ValueError("extracted_text is empty")

    engine = _ParagraphChunkEngine(options)
    all_chunks: list[EpubTranslationChunk] = []

    # Process chapters in canonical spine order (chapter_map is already ordered)
    for chapter in translation_input.chapter_map:
        # Extract pure chapter body from extracted_text using body offsets
        # Validation above ensures these are not None
        body_start = chapter.body_start_offset
        body_end = chapter.body_end_offset
        assert body_start is not None and body_end is not None, "validated above"
        chapter_body = extracted_text[body_start:body_end]

        # Verify the extracted body matches expected length
        expected_len = body_end - body_start
        if len(chapter_body) != expected_len:
            raise ValueError(
                f"Chapter {chapter.chapter_id} body text length mismatch: "
                f"expected {expected_len}, got {len(chapter_body)}"
            )

        # Chunk the chapter body
        chunks = _chunk_chapter_body(chapter_body, chapter, extracted_text, engine)
        all_chunks.extend(chunks)

    # Verify no cross-chapter chunks (invariant)
    for chunk in all_chunks:
        chapter = next(c for c in translation_input.chapter_map if c.chapter_id == chunk.chapter_id)
        chapter_body_start = chapter.body_start_offset
        chapter_body_end = chapter.body_end_offset
        assert chapter_body_start is not None and chapter_body_end is not None
        if chunk.extracted_start_offset < chapter_body_start:
            raise ValueError(
                f"Chunk {chunk.chunk_id} extracted_start_offset ({chunk.extracted_start_offset}) "
                f"before chapter body_start_offset ({chapter_body_start})"
            )
        if chunk.extracted_end_offset > chapter_body_end:
            raise ValueError(
                f"Chunk {chunk.chunk_id} extracted_end_offset ({chunk.extracted_end_offset}) "
                f"after chapter body_end_offset ({chapter_body_end})"
            )

    return tuple(all_chunks)


# Convenience function for direct chapter body chunking (for testing)
def chunk_chapter_body(
    chapter_body: str,
    chapter_boundary: EpubChapterBoundary,
    extracted_text: str,
    options: ChunkingOptions | None = None,
) -> tuple[EpubTranslationChunk, ...]:
    """Chunk a single chapter body directly.

    Useful for testing and incremental processing.
    """
    if options is None:
        options = ChunkingOptions()
    engine = _ParagraphChunkEngine(options)
    return tuple(_chunk_chapter_body(chapter_body, chapter_boundary, extracted_text, engine))
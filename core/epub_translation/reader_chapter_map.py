"""S4 EPUB Reader Chapter Map Builder.

Builds ReaderChapterMap from EpubTranslationResult and EpubTranslationInput.
This is an EPUB-specific mapping layer that does NOT perform translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.epub_translation.contract import (
    EpubTranslationInput,
    EpubTranslationResult,
    EpubChapterResult,
)
from core.epub_translation.reader_models import ChapterBoundary, ReaderChapterMap


class ReaderChapterMapBuildError(ValueError):
    """Error raised when ReaderChapterMap cannot be safely built."""
    pass


# Assembly separator matches S3 runtime assembly logic
_CHAPTER_SEPARATOR = "\n\n"


def _assemble_full_text(chapter_results: tuple[EpubChapterResult, ...]) -> str:
    """Assemble full translated text from chapter results in spine order.

    Includes chapters with aggregate_status in {"success", "incomplete"} that have non-empty assembled_text.
    Failed chapters contribute no content but maintain position in map.
    Final text ends with a single newline.
    """
    parts: list[str] = []
    for chapter_result in chapter_results:
        if chapter_result.aggregate_status in {"success", "incomplete"} and chapter_result.assembled_text:
            parts.append(chapter_result.assembled_text.rstrip("\n"))
    return _CHAPTER_SEPARATOR.join(parts).strip() + "\n" if parts else ""


def _compute_chapter_positions(
    chapter_results: tuple[EpubChapterResult, ...],
    full_text: str,
) -> list[tuple[int, int]]:
    """Compute start/end positions of each chapter in the assembled full_text.

    Returns list of (start_position, end_position) for each chapter in result order.
    Each chapter's range includes its content PLUS the following separator (except last chapter).
    Failed/empty chapters get zero-width position at the appropriate boundary.
    The last chapter's end_position always equals len(full_text).
    """
    if not chapter_results:
        return []

    positions: list[tuple[int, int]] = []
    current_pos = 0

    # First pass: compute content lengths and whether each chapter has content
    chapter_contents: list[str] = []
    chapter_has_content: list[bool] = []
    for chapter_result in chapter_results:
        chapter_content = ""
        has_content = False
        if chapter_result.aggregate_status in {"success", "incomplete"} and chapter_result.assembled_text:
            chapter_content = chapter_result.assembled_text.rstrip("\n")
            has_content = True
        chapter_contents.append(chapter_content)
        chapter_has_content.append(has_content)

    # Second pass: compute positions
    # Each chapter with content gets [start, start + len(content) + separator_len)
    # except the last contentful chapter which extends to len(full_text)
    # Empty chapters get zero-width position at current boundary
    
    # Find indices of contentful chapters
    contentful_indices = [i for i, has in enumerate(chapter_has_content) if has]
    last_contentful_idx = contentful_indices[-1] if contentful_indices else -1

    for idx, (chapter_content, has_content) in enumerate(zip(chapter_contents, chapter_has_content)):
        start_position = current_pos

        if has_content:
            end_position = current_pos + len(chapter_content)
            # Include trailing separator for all but the last contentful chapter
            if idx != last_contentful_idx:
                end_position += len(_CHAPTER_SEPARATOR)
            
            positions.append((start_position, end_position))
            current_pos = end_position
        else:
            # Failed/empty chapter - zero-width position at current boundary
            positions.append((current_pos, current_pos))
            # Position doesn't advance for empty chapters

    # Fix: Last chapter's end_position must equal len(full_text)
    if positions:
        last_start, _ = positions[-1]
        if chapter_has_content[-1]:
            # Last chapter has content - extend to full length (includes trailing \n)
            positions[-1] = (last_start, len(full_text))
        else:
            # Last chapter is empty - position at end of full_text
            positions[-1] = (len(full_text), len(full_text))

    return positions


def _validate_input_chapter_map(input_data: EpubTranslationInput) -> None:
    """Validate that input chapter map is well-formed for mapping."""
    if not input_data.chapter_map:
        raise ReaderChapterMapBuildError("Input chapter_map is empty")

    chapter_ids = set()
    spine_positions = set()

    for chapter in input_data.chapter_map:
        if chapter.chapter_id in chapter_ids:
            raise ReaderChapterMapBuildError(f"Duplicate chapter_id in input: {chapter.chapter_id}")
        chapter_ids.add(chapter.chapter_id)

        if chapter.spine_position in spine_positions:
            raise ReaderChapterMapBuildError(f"Duplicate spine_position in input: {chapter.spine_position}")
        spine_positions.add(chapter.spine_position)


def _validate_result_chapter_results(result: EpubTranslationResult, input_data: EpubTranslationInput) -> None:
    """Validate that result chapter_results correspond to input chapters."""
    if not result.chapter_results:
        raise ReaderChapterMapBuildError("Result chapter_results is empty")

    # Check against ALL input chapters (linear + supplementary)
    input_chapter_ids = {c.chapter_id for c in input_data.chapter_map}
    result_chapter_ids = {cr.chapter_id for cr in result.chapter_results}

    # Check for duplicate chapter_ids in result FIRST (before missing/extra check)
    seen = set()
    for cr in result.chapter_results:
        if cr.chapter_id in seen:
            raise ReaderChapterMapBuildError(f"Duplicate chapter_id in result: {cr.chapter_id}")
        seen.add(cr.chapter_id)

    # Result must contain exactly the same chapters as input (no missing, no extra)
    missing = input_chapter_ids - result_chapter_ids
    extra = result_chapter_ids - input_chapter_ids

    if missing:
        raise ReaderChapterMapBuildError(f"Result missing chapters from input: {sorted(missing)}")
    if extra:
        raise ReaderChapterMapBuildError(f"Result has extra chapters not in input: {sorted(extra)}")

    # Verify chapter_results are in spine order (chapter_order must be 1, 2, 3... sequentially)
    # This enforces canonical spine order in the result
    for i, cr in enumerate(result.chapter_results):
        expected_order = i + 1
        if cr.chapter_order != expected_order:
            raise ReaderChapterMapBuildError(
                f"Chapter order mismatch: position {i} has chapter_order {cr.chapter_order}, expected {expected_order}"
            )


def _validate_chunk_integrity(chapter_result: EpubChapterResult, input_chapter) -> None:
    """Validate chunk integrity within a chapter result.

    Checks:
    - All chunks belong to the correct chapter
    - No duplicate chunk_ids
    - No missing chunks (sequence gaps)
    - No duplicate chunks (same sequence)
    - Chunk ownership matches
    """
    if not chapter_result.chunk_results:
        # Empty chapter should have exactly one empty chunk (validated in S2/S3)
        if input_chapter.word_count == 0:
            return
        raise ReaderChapterMapBuildError(f"Chapter {chapter_result.chapter_id} has no chunk results")

    chunk_ids = set()
    sequences = set()

    for chunk_result in chapter_result.chunk_results:
        # Verify chunk belongs to this chapter
        if not chunk_result.chunk_id.startswith(f"{chapter_result.chapter_id}:"):
            raise ReaderChapterMapBuildError(
                f"Chunk {chunk_result.chunk_id} does not belong to chapter {chapter_result.chapter_id}"
            )

        if chunk_result.chunk_id in chunk_ids:
            raise ReaderChapterMapBuildError(f"Duplicate chunk_id: {chunk_result.chunk_id}")
        chunk_ids.add(chunk_result.chunk_id)

        # Extract sequence from chunk_id (format: chapter_id:chunkXXXX)
        try:
            seq_str = chunk_result.chunk_id.split(":chunk")[-1]
            seq = int(seq_str)
        except (ValueError, IndexError):
            raise ReaderChapterMapBuildError(f"Invalid chunk_id format: {chunk_result.chunk_id}")

        if seq in sequences:
            raise ReaderChapterMapBuildError(f"Duplicate chunk sequence {seq} in chapter {chapter_result.chapter_id}")
        sequences.add(seq)

    # Check for sequence gaps (0, 1, 2, ... n-1)
    if sequences:
        expected_sequences = set(range(len(sequences)))
        if sequences != expected_sequences:
            missing = expected_sequences - sequences
            raise ReaderChapterMapBuildError(
                f"Missing chunk sequences in chapter {chapter_result.chapter_id}: {sorted(missing)}"
            )


def build_epub_reader_chapter_map(
    translation_result: EpubTranslationResult,
    translation_input: EpubTranslationInput,
) -> ReaderChapterMap:
    """Build deterministic ReaderChapterMap from EPUB translation result.

    This is a READ-ONLY mapping operation. It does NOT:
    - Perform translation
    - Call providers
    - Execute runtime
    - Modify input objects

    Args:
        translation_result: EpubTranslationResult from S3 runtime
        translation_input: EpubTranslationInput from S1/S2 (for chapter metadata)

    Returns:
        ReaderChapterMap with immutable ChapterBoundary entries

    Raises:
        ReaderChapterMapBuildError: If mapping cannot be safely established
    """
    # Validate inputs
    _validate_input_chapter_map(translation_input)
    _validate_result_chapter_results(translation_result, translation_input)

    # Build lookup for input chapter metadata (title, source_href, fragment)
    input_chapter_map = {c.chapter_id: c for c in translation_input.chapter_map}

    # Verify all result chapters have corresponding input chapters
    for cr in translation_result.chapter_results:
        if cr.chapter_id not in input_chapter_map:
            raise ReaderChapterMapBuildError(f"Result chapter {cr.chapter_id} not found in input chapter_map")

    # Validate chunk integrity for each chapter
    for cr in translation_result.chapter_results:
        input_chapter = input_chapter_map[cr.chapter_id]
        _validate_chunk_integrity(cr, input_chapter)

    # Assemble full text from successful/incomplete chapters only
    full_text = _assemble_full_text(translation_result.chapter_results)

    # Compute chapter positions in full_text
    positions = _compute_chapter_positions(translation_result.chapter_results, full_text)

    # Build ChapterBoundary entries
    chapters: list[ChapterBoundary] = []

    for idx, chapter_result in enumerate(translation_result.chapter_results):
        input_chapter = input_chapter_map[chapter_result.chapter_id]
        start_position, end_position = positions[idx]

        # Determine chapter title (prefer input title, fallback to assembled text marker or generic)
        chapter_title = input_chapter.title
        if not chapter_title:
            # Try to extract from assembled text if available
            if chapter_result.assembled_text:
                import re
                marker_match = re.search(r"(?:第\s*\d+\s*章|Chapter\s+\d+|CHAPTER\s+\d+)", chapter_result.assembled_text)
                if marker_match:
                    chapter_title = marker_match.group(0).replace(" ", "")
                else:
                    chapter_title = f"第{chapter_result.chapter_order}章"
            else:
                chapter_title = f"第{chapter_result.chapter_order}章"

        chapters.append(ChapterBoundary(
            chapter_id=chapter_result.chapter_id,
            chapter_order=chapter_result.chapter_order - 1,  # ChapterBoundary uses 0-based order
            chapter_title=chapter_title,
            start_position=start_position,
            end_position=end_position,
            scene_ids=(),  # EPUB doesn't have scene IDs in this layer
        ))

    # Validate the chapter map integrity
    _validate_chapter_map_integrity(chapters, full_text)

    return ReaderChapterMap(chapters=tuple(chapters))


def _validate_chapter_map_integrity(chapters: list[ChapterBoundary], full_text: str) -> None:
    """Validate chapter map integrity requirements."""
    if not chapters:
        if full_text:
            raise ReaderChapterMapBuildError("Chapter map is empty but full_text is not empty")
        return

    if chapters[0].start_position != 0:
        raise ReaderChapterMapBuildError(f"First chapter must start at position 0, got {chapters[0].start_position}")

    if chapters[-1].end_position != len(full_text):
        raise ReaderChapterMapBuildError(
            f"Last chapter end_position ({chapters[-1].end_position}) "
            f"must equal full_text length ({len(full_text)})"
        )

    for i, chapter in enumerate(chapters):
        # Allow empty chapters (start == end) but not invalid ranges
        if not (0 <= chapter.start_position <= chapter.end_position <= len(full_text)):
            raise ReaderChapterMapBuildError(
                f"Chapter {chapter.chapter_id} has invalid position: "
                f"[{chapter.start_position}, {chapter.end_position}) "
                f"for full_text length {len(full_text)}"
            )

        if i > 0:
            prev = chapters[i - 1]
            if prev.end_position != chapter.start_position:
                raise ReaderChapterMapBuildError(
                    f"Gap or overlap between chapters: "
                    f"chapter {i - 1} ends at {prev.end_position}, "
                    f"chapter {i} starts at {chapter.start_position}"
                )

    # Verify content reconstruction (only for non-empty chapters)
    reconstructed = "".join(
        full_text[c.start_position:c.end_position]
        for c in chapters
    )
    if reconstructed != full_text:
        raise ReaderChapterMapBuildError("Content preservation invariant violated: reconstructed text != original text")


@dataclass(frozen=True)
class EpubReaderChapterMapResult:
    """Result of building EPUB ReaderChapterMap with additional metadata."""

    reader_chapter_map: ReaderChapterMap
    full_text: str
    chapter_statuses: MappingProxyType[str, str]  # chapter_id -> aggregate_status
    source_hrefs: MappingProxyType[str, str | None]  # chapter_id -> source_href
    fragments: MappingProxyType[str, str | None]  # chapter_id -> fragment


def build_epub_reader_chapter_map_with_metadata(
    translation_result: EpubTranslationResult,
    translation_input: EpubTranslationInput,
) -> EpubReaderChapterMapResult:
    """Build ReaderChapterMap with additional EPUB metadata preserved.

    Returns enriched result containing:
    - ReaderChapterMap (for reader packaging)
    - full_text (assembled translation)
    - chapter_statuses (preserves failed/incomplete state)
    - source_hrefs (preserved from input)
    - fragments (preserved from input)
    """
    reader_chapter_map = build_epub_reader_chapter_map(translation_result, translation_input)
    full_text = _assemble_full_text(translation_result.chapter_results)

    chapter_statuses = {}
    source_hrefs = {}
    fragments = {}

    for cr in translation_result.chapter_results:
        chapter_statuses[cr.chapter_id] = cr.aggregate_status
        input_chapter = translation_input.chapter_map[0]  # fallback
        for ic in translation_input.chapter_map:
            if ic.chapter_id == cr.chapter_id:
                input_chapter = ic
                break
        source_hrefs[cr.chapter_id] = input_chapter.source_href
        fragments[cr.chapter_id] = input_chapter.fragment

    return EpubReaderChapterMapResult(
        reader_chapter_map=reader_chapter_map,
        full_text=full_text,
        chapter_statuses=MappingProxyType(chapter_statuses),
        source_hrefs=MappingProxyType(source_hrefs),
        fragments=MappingProxyType(fragments),
    )
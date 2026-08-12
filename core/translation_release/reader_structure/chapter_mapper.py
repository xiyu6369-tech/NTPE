from __future__ import annotations

import re
from typing import Any

from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap


CHAPTER_PATTERN = re.compile(r"(?:第\s*\d+\s*章|Chapter\s+\d+|CHAPTER\s+\d+)")

# Assembly separator used by RM-8.3 runtime
_CHUNK_SEPARATOR = "\n\n"


def _extract_chapter_title_from_text(text: str, fallback: str) -> str:
    """Extract chapter title from explicit marker in text."""
    match = CHAPTER_PATTERN.search(text)
    if match:
        return match.group(0).replace(" ", "")
    return fallback


def _determine_chapter_identity(
    record: dict,
    explicit_marker: str,
    chapter_order: int,
) -> tuple[str, str]:
    """Determine chapter_id and chapter_title using priority rules.

    Priority 1: RM-8.2 chapter provenance (context_state.boundary.chapter_id)
    Priority 2: Explicit chapter marker
    Priority 3: Deterministic fallback
    """
    context_state = record.get("metadata", {}).get("context_state", {})
    # RM-8.2 runtime places chapter_id inside boundary object
    chapter_id = context_state.get("boundary", {}).get("chapter_id")

    if chapter_id:
        if explicit_marker:
            return chapter_id, explicit_marker
        return chapter_id, f"第{chapter_order}章"

    if explicit_marker:
        marker_chapter_id = explicit_marker.replace(" ", "")
        return marker_chapter_id, explicit_marker

    fallback_id = f"chapter_{chapter_order}"
    fallback_title = f"第{chapter_order}章"
    return fallback_id, fallback_title


def _assemble_txt_body(translated_chunks: list[str]) -> str:
    """Replicate RM-8.3 runtime assembly logic exactly.

    This MUST match lts/txt_translation_runtime.py assembly:
    final_text = "\n\n".join(translated_chunks).strip() + "\n"
    """
    return _CHUNK_SEPARATOR.join(translated_chunks).strip() + "\n"


def _compute_chunk_positions(translated_chunks: list[str]) -> list[tuple[int, int]]:
    """Compute start/end positions of each chunk in the assembled txt_body.

    Returns list of (start_position, end_position) for each chunk.

    Must replicate the exact assembly logic:
    1. Join with "\n\n"
    2. .strip() - removes leading/trailing whitespace
    3. + "\n" - adds trailing newline
    """
    if not translated_chunks:
        return []

    # Step 1: Join with separator
    joined = _CHUNK_SEPARATOR.join(translated_chunks)

    # Step 2: Find positions in the joined string (before strip)
    positions: list[tuple[int, int]] = []
    current_pos = 0

    for i, chunk in enumerate(translated_chunks):
        start = current_pos
        current_pos += len(chunk)
        end = current_pos
        positions.append((start, end))

        # Add separator after each chunk except the last
        if i < len(translated_chunks) - 1:
            current_pos += len(_CHUNK_SEPARATOR)

    # Step 3: Apply strip() - find how many leading/trailing chars were stripped
    stripped = joined.strip()
    leading_stripped = len(joined) - len(joined.lstrip())
    trailing_stripped = len(joined) - len(joined.rstrip())

    # Step 4: Adjust positions for strip and add trailing newline
    # The final txt_body is stripped + "\n"
    adjusted_positions: list[tuple[int, int]] = []
    for start, end in positions:
        # Adjust for leading strip
        adj_start = max(0, start - leading_stripped)
        adj_end = max(0, end - leading_stripped)
        # Adjust for trailing strip (only affects positions after the stripped trailing part)
        # The trailing strip removes chars from the end, so positions before the trailing
        # stripped region are unaffected, but the total length changes
        adjusted_positions.append((adj_start, adj_end))

    return adjusted_positions


def build_reader_chapter_map(
    *,
    txt_body: str,
    translated_chunks: list[str],
    chunk_records: list[dict],
    skip_assembly_validation: bool = False,
) -> ReaderChapterMap:
    """Build deterministic chapter mapping from RM-8.3 TXT body and RM-8.2 chunk records.

    This is a READ-ONLY mapping operation. The txt_body is NOT modified.

    Args:
        txt_body: The final RM-8.3 TXT body (source of truth, not modified)
        translated_chunks: List of translated chunk texts in order (used for position computation)
        chunk_records: RM-8.2 chunk records with context_state metadata (provenance only)
        skip_assembly_validation: If True, skip verification that txt_body matches
            assembled translated_chunks. Used when txt_body has been polished/processed
            after assembly (e.g., canonicalization, punctuation normalization).

    Returns:
        ReaderChapterMap with immutable ChapterBoundary entries

    Raises:
        ValueError: If chapter mapping cannot be safely established
    """
    if not chunk_records:
        if not txt_body:
            return ReaderChapterMap(chapters=())
        raise ValueError("Cannot build chapter map: no chunk records provided for non-empty txt_body")

    if not txt_body:
        raise ValueError("Cannot build chapter map: empty txt_body")

    if len(translated_chunks) != len(chunk_records):
        raise ValueError(
            f"translated_chunks length ({len(translated_chunks)}) "
            f"must match chunk_records length ({len(chunk_records)})"
        )

    # Verify txt_body matches assembled translated_chunks (defense in depth)
    # Skip if txt_body has been post-processed (polished, canonicalized)
    if not skip_assembly_validation:
        expected_txt = _assemble_txt_body(translated_chunks)
        if txt_body != expected_txt:
            raise ValueError(
                "txt_body does not match assembled translated_chunks. "
                "txt_body must be the exact output of RM-8.3 assembly."
            )

    chapter_data: dict[str, dict[str, Any]] = {}
    chapter_order: list[str] = []

    # Compute chunk positions in assembled text
    chunk_positions = _compute_chunk_positions(translated_chunks)

    chapter_boundaries: list[ChapterBoundary] = []

    prev_chapter_id: str | None = None

    for record_idx, record in enumerate(chunk_records):
        chunk_start, chunk_end = chunk_positions[record_idx]
        context_state = record.get("metadata", {}).get("context_state", {})
        boundary_type = context_state.get("boundary", {}).get("type", "same_scene")
        scene_id = context_state.get("scene_id", f"scene_{record_idx + 1}")
        # RM-8.2 provenance: chapter_id is inside boundary object
        current_chapter_id = context_state.get("boundary", {}).get("chapter_id")

        # Chapter boundary if:
        # 1. Explicit chapter_transition boundary
        # 2. Scene transition where chapter_id changes from previous
        is_chapter_boundary = (
            boundary_type == "chapter_transition"
            or (boundary_type == "scene_transition" and current_chapter_id != prev_chapter_id)
        )

        if is_chapter_boundary or (not chapter_boundaries and record_idx == 0):
            if chapter_boundaries:
                prev_chapter = chapter_boundaries[-1]
                prev_chapter_dict = chapter_data[prev_chapter.chapter_id]
                if "end_position" not in prev_chapter_dict:
                    prev_chapter_dict["end_position"] = chunk_start

            explicit_marker = ""
            if "source" in record and isinstance(record["source"], dict):
                source_text = record["source"].get("chunk_text", "")
                if source_text:
                    explicit_marker = _extract_chapter_title_from_text(source_text, "")

            chapter_order_num = len(chapter_order)
            chapter_id, chapter_title = _determine_chapter_identity(
                record, explicit_marker, chapter_order_num
            )

            if chapter_id not in chapter_data:
                chapter_data[chapter_id] = {
                    "scene_ids": set(),
                    "start_position": chunk_start,
                    "chapter_title": chapter_title,
                    "chapter_order": chapter_order_num,
                }
                chapter_order.append(chapter_id)

            chapter_data[chapter_id]["scene_ids"].add(scene_id)

            if not chapter_boundaries or chapter_boundaries[-1].chapter_id != chapter_id:
                chapter_boundaries.append(ChapterBoundary(
                    chapter_id=chapter_id,
                    chapter_order=chapter_data[chapter_id]["chapter_order"],
                    chapter_title=chapter_data[chapter_id]["chapter_title"],
                    start_position=chapter_data[chapter_id]["start_position"],
                    end_position=-1,
                    scene_ids=(),
                ))

        elif chapter_boundaries:
            last_chapter_id = chapter_boundaries[-1].chapter_id
            chapter_data[last_chapter_id]["scene_ids"].add(scene_id)
            chapter_boundaries[-1] = ChapterBoundary(
                chapter_id=chapter_boundaries[-1].chapter_id,
                chapter_order=chapter_boundaries[-1].chapter_order,
                chapter_title=chapter_boundaries[-1].chapter_title,
                start_position=chapter_boundaries[-1].start_position,
                end_position=chapter_boundaries[-1].end_position,
                scene_ids=chapter_boundaries[-1].scene_ids + (scene_id,),
            )

        prev_chapter_id = current_chapter_id

    if chapter_boundaries:
        last_chapter = chapter_boundaries[-1]
        last_chapter_dict = chapter_data[last_chapter.chapter_id]
        last_chapter_dict["end_position"] = len(txt_body)

    final_chapters: list[ChapterBoundary] = []
    for chapter_id in chapter_order:
        data = chapter_data[chapter_id]
        if "end_position" not in data:
            data["end_position"] = len(txt_body)

        final_chapters.append(ChapterBoundary(
            chapter_id=chapter_id,
            chapter_order=data["chapter_order"],
            chapter_title=data["chapter_title"],
            start_position=data["start_position"],
            end_position=data["end_position"],
            scene_ids=tuple(sorted(data["scene_ids"])),
        ))

    _validate_chapter_map(final_chapters, txt_body)

    return ReaderChapterMap(chapters=tuple(final_chapters))


def _validate_chapter_map(chapters: list[ChapterBoundary], txt_body: str) -> None:
    """Validate chapter map integrity requirements."""
    if not chapters:
        if txt_body:
            raise ValueError("Chapter map is empty but txt_body is not empty")
        return

    if chapters[0].start_position != 0:
        raise ValueError(f"First chapter must start at position 0, got {chapters[0].start_position}")

    if chapters[-1].end_position != len(txt_body):
        raise ValueError(
            f"Last chapter end_position ({chapters[-1].end_position}) "
            f"must equal txt_body length ({len(txt_body)})"
        )

    for i, chapter in enumerate(chapters):
        if not (0 <= chapter.start_position < chapter.end_position <= len(txt_body)):
            raise ValueError(
                f"Chapter {chapter.chapter_id} has invalid position: "
                f"[{chapter.start_position}, {chapter.end_position}) "
                f"for txt_body length {len(txt_body)}"
            )

        if i > 0:
            prev = chapters[i - 1]
            if prev.end_position != chapter.start_position:
                raise ValueError(
                    f"Gap or overlap between chapters: "
                    f"chapter {i - 1} ends at {prev.end_position}, "
                    f"chapter {i} starts at {chapter.start_position}"
                )

    reconstructed = "".join(
        txt_body[c.start_position:c.end_position]
        for c in chapters
    )
    if reconstructed != txt_body:
        raise ValueError("Content preservation invariant violated: reconstructed text != original text")
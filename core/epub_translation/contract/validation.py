"""EPUB Translation Contract Validators — S1.

Deterministic validators for EPUB translation contract models.
All validators are pure functions with no side effects.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from types import MappingProxyType

from .models import (
    EpubTranslationInput,
    EpubChapterBoundary,
    EpubTranslationChunk,
    EpubChunkResult,
    EpubChapterResult,
    EpubTranslationResult,
)


class ContractValidationError(ValueError):
    """Contract validation failure."""
    pass


# Regex patterns
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.I)
_CHAPTER_ID_RE = re.compile(r"^ch\d{4}$")
_CHUNK_ID_RE = re.compile(r"^[\w\-:]+$")  # Allow alphanumeric, dash, colon, underscore


def validate_sha256(value: str, field_name: str) -> None:
    """Validate SHA256 hex digest format."""
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ContractValidationError(f"{field_name} must be a 64-char hex SHA256 digest: {value}")


def validate_chapter_id(value: str, field_name: str) -> None:
    """Validate chapter_id format (chXXXX)."""
    if not isinstance(value, str) or not _CHAPTER_ID_RE.fullmatch(value):
        raise ContractValidationError(f"{field_name} must match chXXXX format: {value}")


def validate_chunk_id(value: str, field_name: str) -> None:
    """Validate chunk_id format (flexible alphanumeric with separators)."""
    if not isinstance(value, str) or not _CHUNK_ID_RE.fullmatch(value):
        raise ContractValidationError(f"{field_name} must be valid chunk identifier: {value}")


def validate_non_negative_int(value: int, field_name: str) -> None:
    """Validate non-negative integer."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ContractValidationError(f"{field_name} must be a non-negative integer: {value}")


def validate_positive_int(value: int, field_name: str) -> None:
    """Validate positive integer (>= 1)."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractValidationError(f"{field_name} must be a positive integer: {value}")


def validate_chapter_boundary(boundary: EpubChapterBoundary) -> None:
    """Validate a single chapter boundary."""
    validate_positive_int(boundary.index, "chapter_boundary.index")
    validate_positive_int(boundary.spine_position, "chapter_boundary.spine_position")
    validate_non_negative_int(boundary.start_offset, "chapter_boundary.start_offset")
    validate_non_negative_int(boundary.end_offset, "chapter_boundary.end_offset")
    if boundary.end_offset < boundary.start_offset:
        raise ContractValidationError(
            f"chapter_boundary.end_offset ({boundary.end_offset}) < start_offset ({boundary.start_offset})"
        )
    if boundary.body_start_offset is not None:
        validate_non_negative_int(boundary.body_start_offset, "chapter_boundary.body_start_offset")
    if boundary.body_end_offset is not None:
        validate_non_negative_int(boundary.body_end_offset, "chapter_boundary.body_end_offset")
    if boundary.body_start_offset is not None and boundary.body_end_offset is not None:
        if boundary.body_end_offset < boundary.body_start_offset:
            raise ContractValidationError(
                f"chapter_boundary.body_end_offset ({boundary.body_end_offset}) < body_start_offset ({boundary.body_start_offset})"
            )
    # body offsets must be within marker-inclusive range if available
    if boundary.body_start_offset is not None:
        if boundary.body_start_offset < boundary.start_offset:
            raise ContractValidationError(
                f"body_start_offset ({boundary.body_start_offset}) < start_offset ({boundary.start_offset})"
            )
        if boundary.body_start_offset > boundary.end_offset:
            raise ContractValidationError(
                f"body_start_offset ({boundary.body_start_offset}) > end_offset ({boundary.end_offset})"
            )
    if boundary.body_end_offset is not None:
        if boundary.body_end_offset < boundary.start_offset:
            raise ContractValidationError(
                f"body_end_offset ({boundary.body_end_offset}) < start_offset ({boundary.start_offset})"
            )
        if boundary.body_end_offset > boundary.end_offset:
            raise ContractValidationError(
                f"body_end_offset ({boundary.body_end_offset}) > end_offset ({boundary.end_offset})"
            )
    # For non-empty chapters, body_end should be >= body_start
    if boundary.word_count > 0:
        if boundary.body_start_offset is not None and boundary.body_end_offset is not None:
            if boundary.body_end_offset < boundary.body_start_offset:
                raise ContractValidationError(
                    f"chapter_boundary.body_end_offset ({boundary.body_end_offset}) < body_start_offset ({boundary.body_start_offset})"
                )
    validate_non_negative_int(boundary.word_count, "chapter_boundary.word_count")
    if boundary.status not in {"linear", "supplementary"}:
        raise ContractValidationError(f"chapter_boundary.status must be 'linear' or 'supplementary': {boundary.status}")


def validate_epub_translation_input(input_data: EpubTranslationInput) -> None:
    """Validate complete EPUB translation input contract."""
    # Source EPUB identity
    validate_sha256(input_data.original_hash, "original_hash")

    # Extraction status
    valid_statuses = {"success", "partial", "manual_review_required", "blocked"}
    if input_data.extraction_status not in valid_statuses:
        raise ContractValidationError(f"extraction_status invalid: {input_data.extraction_status}")

    # Chapter map structural validation
    if not input_data.chapter_map:
        raise ContractValidationError("chapter_map must not be empty")

    chapter_ids = set()
    spine_positions = set()
    prev_spine_pos = 0

    for i, chapter in enumerate(input_data.chapter_map):
        validate_chapter_boundary(chapter)

        # Chapter ID uniqueness
        if chapter.chapter_id in chapter_ids:
            raise ContractValidationError(f"Duplicate chapter_id: {chapter.chapter_id}")
        chapter_ids.add(chapter.chapter_id)

        # Spine position uniqueness and order
        if chapter.spine_position in spine_positions:
            raise ContractValidationError(f"Duplicate spine_position: {chapter.spine_position}")
        spine_positions.add(chapter.spine_position)

        if chapter.spine_position <= prev_spine_pos:
            raise ContractValidationError(
                f"chapter_map spine positions not strictly increasing: "
                f"chapter {i} has spine_position {chapter.spine_position}, previous {prev_spine_pos}"
            )
        prev_spine_pos = chapter.spine_position

        # Chapter index matches iteration order (1-based)
        if chapter.index != i + 1:
            raise ContractValidationError(
                f"chapter_map index mismatch: position {i} has chapter.index {chapter.index}"
            )

    # Validate toc_entries if present
    for toc in input_data.toc_entries:
        if not isinstance(toc.href, str) or not toc.href:
            raise ContractValidationError("toc_entries href must be non-empty string")
        if not isinstance(toc.title, str):
            raise ContractValidationError("toc_entries title must be string")
        if not isinstance(toc.level, int) or toc.level < 0:
            raise ContractValidationError("toc_entries level must be non-negative int")

    # Validate resources
    for res in input_data.resources:
        if not isinstance(res.type, str) or not res.type:
            raise ContractValidationError("resource type must be non-empty string")
        if not isinstance(res.href, str) or not res.href:
            raise ContractValidationError("resource href must be non-empty string")


def validate_epub_translation_chunk(chunk: EpubTranslationChunk) -> None:
    """Validate a single translation chunk."""
    validate_chunk_id(chunk.chunk_id, "chunk.chunk_id")
    validate_chapter_id(chunk.chapter_id, "chunk.chapter_id")
    validate_non_negative_int(chunk.chapter_order, "chunk.chapter_order")
    validate_non_negative_int(chunk.chunk_sequence, "chunk.chunk_sequence")
    validate_non_negative_int(chunk.extracted_start_offset, "chunk.extracted_start_offset")
    validate_non_negative_int(chunk.extracted_end_offset, "chunk.extracted_end_offset")
    validate_non_negative_int(chunk.body_start_offset, "chunk.body_start_offset")
    validate_non_negative_int(chunk.body_end_offset, "chunk.body_end_offset")

    if chunk.extracted_end_offset < chunk.extracted_start_offset:
        raise ContractValidationError(
            f"chunk extracted_end_offset ({chunk.extracted_end_offset}) < extracted_start_offset ({chunk.extracted_start_offset})"
        )
    if chunk.body_end_offset < chunk.body_start_offset:
        raise ContractValidationError(
            f"chunk body_end_offset ({chunk.body_end_offset}) < body_start_offset ({chunk.body_start_offset})"
        )
    # Body offsets must be within extracted range
    if chunk.body_start_offset < chunk.extracted_start_offset:
        raise ContractValidationError(
            f"chunk body_start_offset ({chunk.body_start_offset}) < extracted_start_offset ({chunk.extracted_start_offset})"
        )
    if chunk.body_end_offset > chunk.extracted_end_offset:
        raise ContractValidationError(
            f"chunk body_end_offset ({chunk.body_end_offset}) > extracted_end_offset ({chunk.extracted_end_offset})"
        )


def validate_epub_chunk_result(result: EpubChunkResult) -> None:
    """Validate a single chunk result."""
    validate_chunk_id(result.chunk_id, "chunk_result.chunk_id")

    if result.status not in EpubChunkResult.VALID_STATUSES:
        raise ContractValidationError(f"Invalid chunk status: {result.status}")

    validate_non_negative_int(result.attempt, "chunk_result.attempt")

    if result.qa_report is not None:
        if not isinstance(result.qa_report, MappingProxyType):
            raise ContractValidationError("chunk_result.qa_report must be MappingProxyType")
        # Additional QA report structure validation could go here


def validate_epub_chapter_result(result: EpubChapterResult) -> None:
    """Validate a single chapter result."""
    validate_chapter_id(result.chapter_id, "chapter_result.chapter_id")
    validate_positive_int(result.chapter_order, "chapter_result.chapter_order")

    if result.aggregate_status not in EpubChapterResult.VALID_STATUSES:
        raise ContractValidationError(f"Invalid chapter aggregate status: {result.aggregate_status}")

    validate_non_negative_int(result.success_count, "chapter_result.success_count")
    validate_non_negative_int(result.failed_count, "chapter_result.failed_count")
    validate_non_negative_int(result.skipped_count, "chapter_result.skipped_count")

    # Verify chunk results
    chunk_ids = set()
    for chunk_res in result.chunk_results:
        validate_epub_chunk_result(chunk_res)
        if chunk_res.chunk_id in chunk_ids:
            raise ContractValidationError(f"Duplicate chunk_id in chapter results: {chunk_res.chunk_id}")
        chunk_ids.add(chunk_res.chunk_id)

    # Verify counts match
    actual_success = sum(1 for c in result.chunk_results if c.status == "success")
    actual_failed = sum(1 for c in result.chunk_results if c.status == "failed")
    actual_skipped = sum(1 for c in result.chunk_results if c.status == "skipped")
    actual_dry_run = sum(1 for c in result.chunk_results if c.status == "dry_run")

    if result.success_count != actual_success:
        raise ContractValidationError(
            f"chapter success_count mismatch: declared={result.success_count}, actual={actual_success}"
        )
    if result.failed_count != actual_failed:
        raise ContractValidationError(
            f"chapter failed_count mismatch: declared={result.failed_count}, actual={actual_failed}"
        )
    if result.skipped_count != actual_skipped:
        raise ContractValidationError(
            f"chapter skipped_count mismatch: declared={result.skipped_count}, actual={actual_skipped}"
        )


def validate_epub_translation_result(result: EpubTranslationResult) -> None:
    """Validate complete EPUB translation result."""
    if result.aggregate_status not in EpubTranslationResult.VALID_STATUSES:
        raise ContractValidationError(f"Invalid aggregate status: {result.aggregate_status}")

    validate_non_negative_int(result.success_count, "result.success_count")
    validate_non_negative_int(result.failed_count, "result.failed_count")
    validate_non_negative_int(result.skipped_count, "result.skipped_count")

    # Chapter results must be in spine order and unique
    chapter_ids = set()
    chapter_orders = set()

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for chapter_res in result.chapter_results:
        validate_epub_chapter_result(chapter_res)

        if chapter_res.chapter_id in chapter_ids:
            raise ContractValidationError(f"Duplicate chapter_id in result: {chapter_res.chapter_id}")
        chapter_ids.add(chapter_res.chapter_id)

        if chapter_res.chapter_order in chapter_orders:
            raise ContractValidationError(f"Duplicate chapter_order in result: {chapter_res.chapter_order}")
        chapter_orders.add(chapter_res.chapter_order)

        # Chapter order must be sequential starting from 1 (spine order)
        expected_order = len(chapter_orders)  # 1-based
        if chapter_res.chapter_order != expected_order:
            raise ContractValidationError(
                f"chapter order mismatch: expected chapter_order {expected_order} at position {len(chapter_orders)}, got {chapter_res.chapter_order}"
            )

        total_success += chapter_res.success_count
        total_failed += chapter_res.failed_count
        total_skipped += chapter_res.skipped_count

    # Verify aggregate counts match
    if result.success_count != total_success:
        raise ContractValidationError(
            f"result success_count mismatch: declared={result.success_count}, actual={total_success}"
        )
    if result.failed_count != total_failed:
        raise ContractValidationError(
            f"result failed_count mismatch: declared={result.failed_count}, actual={total_failed}"
        )
    if result.skipped_count != total_skipped:
        raise ContractValidationError(
            f"result skipped_count mismatch: declared={result.skipped_count}, actual={total_skipped}"
        )

    # SUCCESS status contract: ALL required linear chapters succeed, NO required chunk failed
    if result.aggregate_status == "success":
        for chapter_res in result.chapter_results:
            if chapter_res.aggregate_status != "success":
                raise ContractValidationError(
                    f"aggregate_status='success' but chapter {chapter_res.chapter_id} has status={chapter_res.aggregate_status}"
                )
            if chapter_res.failed_count > 0:
                raise ContractValidationError(
                    f"aggregate_status='success' but chapter {chapter_res.chapter_id} has failed chunks"
                )
            # Also verify no skipped/dry_run chunks if strict success required
            for chunk_res in chapter_res.chunk_results:
                if chunk_res.status != "success":
                    raise ContractValidationError(
                        f"aggregate_status='success' but chunk {chunk_res.chunk_id} has status={chunk_res.status}"
                    )

    # INCOMPLETE/FAILED must not claim complete success
    if result.aggregate_status in {"incomplete", "failed"}:
        if result.failed_count == 0 and result.skipped_count == 0:
            raise ContractValidationError(
                f"aggregate_status='{result.aggregate_status}' but no failed/skipped chunks found"
            )


def validate_chunk_ownership(
    input_data: EpubTranslationInput,
    chunks: tuple[EpubTranslationChunk, ...]
) -> None:
    """Validate chunks against input chapter map.

    Ensures:
    - Every chunk belongs to a known chapter
    - No chunk crosses chapter boundaries
    - Chunk sequence is deterministic within chapter
    """
    chapter_map = {c.chapter_id: c for c in input_data.chapter_map}
    chunk_ids = set()

    for chunk in chunks:
        validate_epub_translation_chunk(chunk)

        if chunk.chunk_id in chunk_ids:
            raise ContractValidationError(f"Duplicate chunk_id: {chunk.chunk_id}")
        chunk_ids.add(chunk.chunk_id)

        # Chapter must exist
        if chunk.chapter_id not in chapter_map:
            raise ContractValidationError(f"Chunk {chunk.chunk_id} references unknown chapter: {chunk.chapter_id}")

        chapter = chapter_map[chunk.chapter_id]

        # Chapter order must match
        if chunk.chapter_order != chapter.spine_position:
            raise ContractValidationError(
                f"Chunk {chunk.chunk_id} chapter_order ({chunk.chapter_order}) "
                f"does not match chapter spine_position ({chapter.spine_position})"
            )

        # Offsets must be within chapter's marker-inclusive range
        if chunk.extracted_start_offset < chapter.start_offset:
            raise ContractValidationError(
                f"Chunk {chunk.chunk_id} extracted_start_offset ({chunk.extracted_start_offset}) "
                f"before chapter start_offset ({chapter.start_offset})"
            )
        if chunk.extracted_end_offset > chapter.end_offset:
            raise ContractValidationError(
                f"Chunk {chunk.chunk_id} extracted_end_offset ({chunk.extracted_end_offset}) "
                f"after chapter end_offset ({chapter.end_offset})"
            )

        # Empty chapter must produce exactly one empty chunk
        if chapter.word_count == 0:
            chapter_chunks = [c for c in chunks if c.chapter_id == chapter.chapter_id]
            if len(chapter_chunks) != 1:
                raise ContractValidationError(
                    f"Empty chapter {chapter.chapter_id} must produce exactly one chunk, got {len(chapter_chunks)}"
                )
            empty_chunk = chapter_chunks[0]
            if empty_chunk.source_text != "":
                raise ContractValidationError(
                    f"Empty chapter chunk must have empty source_text, got: {empty_chunk.source_text!r}"
                )

    # After processing all chunks, verify that all empty chapters have exactly one chunk
    for chapter in input_data.chapter_map:
        if chapter.word_count == 0:
            chapter_chunks = [c for c in chunks if c.chapter_id == chapter.chapter_id]
            if len(chapter_chunks) != 1:
                raise ContractValidationError(
                    f"Empty chapter {chapter.chapter_id} must produce exactly one chunk, got {len(chapter_chunks)}"
                )


def validate_no_cross_chapter_chunks(chunks: tuple[EpubTranslationChunk, ...]) -> None:
    """Ensure no chunk spans multiple chapters.

    This is enforced by chunk_ownership validation, but provides explicit check.
    """
    # Chunks are already validated to belong to exactly one chapter each
    # This function is a no-op but documents the invariant
    pass


def validate_complete_contract(
    input_data: EpubTranslationInput,
    chunks: tuple[EpubTranslationChunk, ...],
    result: EpubTranslationResult | None = None
) -> None:
    """Full contract validation: input -> chunks -> (optional) result.

    Call this after translation to verify entire pipeline contract.
    """
    validate_epub_translation_input(input_data)
    validate_chunk_ownership(input_data, chunks)

    if result is not None:
        validate_epub_translation_result(result)

        # Verify result chapters correspond to input chapters
        input_linear_ids = {c.chapter_id for c in input_data.linear_chapters}
        result_ids = {cr.chapter_id for cr in result.chapter_results}

        if result_ids != input_linear_ids:
            missing = input_linear_ids - result_ids
            extra = result_ids - input_linear_ids
            msg_parts = []
            if missing:
                msg_parts.append(f"missing chapters: {sorted(missing)}")
            if extra:
                msg_parts.append(f"extra chapters: {sorted(extra)}")
            raise ContractValidationError("Result chapters do not match input linear chapters: " + "; ".join(msg_parts))

        # Verify chapter order matches spine order
        for i, chapter_res in enumerate(result.chapter_results):
            if chapter_res.chapter_order != i + 1:
                raise ContractValidationError(
                    f"Result chapter order mismatch: position {i} has chapter_order {chapter_res.chapter_order}"
                )
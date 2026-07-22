from dataclasses import FrozenInstanceError

import pytest

from core.book_chunking import (
    BookChunkPlanner,
    BookChunkPlan,
    ChunkBoundary,
    ChunkPlanningFinding,
    TranslationChunk,
)
from core.book_segmentation import BookStructureSegmenter


def _plan() -> BookChunkPlan:
    segmentation = BookStructureSegmenter().segment_text(
        "Chapter 1\nShort text.", source_name="book.txt"
    )
    return BookChunkPlanner().plan(
        segmentation,
        minimum_chunk_size=30,
        target_chunk_size=40,
        maximum_chunk_size=50,
    )


def test_formal_models_and_nested_values_are_frozen() -> None:
    plan = _plan()
    assert isinstance(plan.chunks, tuple)
    assert isinstance(plan.findings, tuple)
    assert isinstance(plan.chunks[0], TranslationChunk)
    assert isinstance(plan.findings[0], ChunkPlanningFinding)
    assert isinstance(plan.chunks[0].section_indices, tuple)
    with pytest.raises(FrozenInstanceError):
        plan.status = "blocked"
    with pytest.raises(FrozenInstanceError):
        plan.chunks[0].text = "changed"
    with pytest.raises(FrozenInstanceError):
        plan.findings[0].message = "changed"


def test_chunk_boundary_is_frozen() -> None:
    boundary = ChunkBoundary(0, 10, 0, 0, 10, "paragraph")
    with pytest.raises(FrozenInstanceError):
        boundary.boundary_type = "line"


def test_chunk_model_counts_and_fingerprint_are_consistent() -> None:
    chunk = _plan().chunks[0]
    assert chunk.character_count == len(chunk.text)
    assert chunk.source_character_end - chunk.source_character_start == len(chunk.text)
    assert chunk.non_whitespace_character_count == sum(not c.isspace() for c in chunk.text)
    assert chunk.first_section_index == chunk.section_indices[0]
    assert chunk.last_section_index == chunk.section_indices[-1]

from dataclasses import FrozenInstanceError

import pytest

from core.book_segmentation import (
    BookSection,
    BookStructureSegmenter,
    ChapterHeading,
    SegmentationFinding,
)


def test_all_nested_models_and_result_are_frozen_and_collections_are_tuples() -> None:
    result = BookStructureSegmenter().segment_text("Chapter 1\nText", source_name="book.txt")
    assert isinstance(result.sections, tuple)
    assert isinstance(result.findings, tuple)
    assert isinstance(result.sections[0], BookSection)
    assert isinstance(result.sections[0].heading, ChapterHeading)
    assert all(isinstance(item, SegmentationFinding) for item in result.findings)
    with pytest.raises(FrozenInstanceError):
        result.status = "blocked"
    with pytest.raises(FrozenInstanceError):
        result.sections[0].text = "changed"
    with pytest.raises(FrozenInstanceError):
        result.sections[0].heading.text = "changed"
    with pytest.raises(FrozenInstanceError):
        result.findings[0].message = "changed"


def test_model_counts_and_heading_coordinates_are_consistent() -> None:
    text = "  Chapter 1  \nA b\t\n"
    result = BookStructureSegmenter().segment_text(text, source_name="book.txt")
    section = result.sections[0]
    assert section.character_start == 0
    assert section.character_end == len(text)
    assert section.character_count == len(text)
    assert section.non_whitespace_character_count == sum(not c.isspace() for c in text)
    assert section.heading is not None
    assert section.heading.text == "  Chapter 1  "
    assert section.heading.line_index == 0
    assert section.heading.character_start == 0
    assert section.heading.character_end == len("  Chapter 1  ")

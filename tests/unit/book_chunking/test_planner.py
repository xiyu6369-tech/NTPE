from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import replace

import pytest

from core.book_chunking import BookChunkPlanner
from core.book_chunking.errors import SegmentationConsistencyError
from core.book_chunking.policy import DEFAULT_POLICY
from core.book_segmentation import BookStructureSegmenter


SEGMENTER = BookStructureSegmenter()
PLANNER = BookChunkPlanner()


def _segmentation(text: str):
    return SEGMENTER.segment_text(text, source_name="novel.txt")


def _plan(text: str, minimum: int = 20, target: int = 40, maximum: int = 60):
    return PLANNER.plan(
        _segmentation(text),
        minimum_chunk_size=minimum,
        target_chunk_size=target,
        maximum_chunk_size=maximum,
    )


@pytest.mark.parametrize(
    "text",
    [
        "Chapter 1\nShort text.",
        "Chapter 1\n" + "a" * 30 + "\n\n" + "b" * 80,
        "Chapter 1\r\n" + "a" * 35 + "\r\n\r\n" + "b" * 90 + "\r\n",
        "  Chapter 1  \n e\u0301 text  \n",
        "Chapter 1\nNo terminal newline",
        "Chapter 1\nTerminal newline\n",
    ],
)
def test_reconstruction_offsets_and_source_slices_are_lossless(text: str) -> None:
    plan = _plan(text)
    assert plan.reconstruct_text() == text
    assert plan.covered_character_count == plan.character_count == len(text)
    assert plan.coverage_ratio == 1.0
    assert plan.chunks[0].source_character_start == 0
    assert plan.chunks[-1].source_character_end == len(text)
    for index, chunk in enumerate(plan.chunks):
        assert chunk.index == index
        assert chunk.text == text[chunk.source_character_start:chunk.source_character_end]
        assert chunk.character_count <= plan.maximum_chunk_size
        if index:
            assert plan.chunks[index - 1].source_character_end == chunk.source_character_start


def test_empty_segmentation_is_a_valid_manual_review_plan() -> None:
    plan = PLANNER.plan(_segmentation(""))
    assert plan.chunks == ()
    assert plan.chunk_count == 0
    assert plan.reconstruct_text() == ""
    assert plan.coverage_ratio == 1.0
    assert plan.status == plan.action == "manual_review"
    assert "EMPTY_CONTENT" in {item.code for item in plan.findings}


def test_short_chapter_remains_whole_and_heading_is_in_first_chunk() -> None:
    text = "Chapter 1\nA short chapter."
    plan = _plan(text, 5, 20, 40)
    assert plan.chunk_count == 1
    assert plan.chunks[0].text == text
    assert plan.chunks[0].heading_text == "Chapter 1"
    assert plan.chunks[0].starts_at_section_boundary
    assert plan.chunks[0].ends_at_section_boundary


def test_multiple_short_structured_sections_merge_without_reordering() -> None:
    text = "Chapter 1\nOne.\nChapter 2\nTwo."
    plan = _plan(text, 5, 80, 100)
    assert plan.chunk_count == 1
    assert plan.chunks[0].section_indices == (0, 1)
    assert plan.chunks[0].first_section_index == 0
    assert plan.chunks[0].last_section_index == 1
    assert "MULTI_SECTION_CHUNK" in {item.code for item in plan.findings}


def test_front_matter_is_preserved_but_not_merged_with_first_chapter() -> None:
    text = "Book title\n\nChapter 1\nText."
    plan = _plan(text, 5, 80, 100)
    assert plan.chunk_count == 2
    assert plan.chunks[0].section_indices == (0,)
    assert plan.chunks[1].section_indices == (1,)
    assert plan.reconstruct_text() == text


def test_heading_only_section_is_legal() -> None:
    plan = _plan("Chapter 1", 2, 10, 20)
    assert plan.chunk_count == 1
    assert plan.chunks[0].heading_text == "Chapter 1"


def test_unclassified_source_is_planned_but_requires_manual_review() -> None:
    plan = _plan("plain unstructured source " * 8, 20, 40, 60)
    assert plan.reconstruct_text() == "plain unstructured source " * 8
    assert plan.status == plan.action == "manual_review"
    assert "NO_STRUCTURED_SECTIONS" in {item.code for item in plan.findings}


def test_paragraph_boundary_has_highest_priority() -> None:
    text = "Chapter 1\n" + "a" * 22 + "\n\n" + "b" * 80 + "."
    plan = _plan(text)
    assert plan.chunks[0].boundary_reason == "paragraph"
    assert plan.chunks[0].text.endswith("\n\n")


def test_sentence_boundary_is_used_without_paragraph_boundary() -> None:
    text = "Chapter 1\n" + "a" * 25 + "。」" + "b" * 80
    plan = _plan(text)
    assert plan.chunks[0].boundary_reason == "sentence"
    assert plan.chunks[0].text.endswith("。」")


def test_line_boundary_is_used_without_paragraph_or_sentence() -> None:
    text = "Chapter 1\n" + "a" * 25 + "\n" + "b" * 80
    plan = _plan(text)
    assert plan.chunks[0].boundary_reason == "line"
    assert plan.chunks[0].text.endswith("\n")


def test_hard_limit_is_last_resort_and_produces_finding() -> None:
    text = "Chapter 1\n" + "x" * 160
    plan = _plan(text)
    assert "hard_limit" in {chunk.boundary_reason for chunk in plan.chunks}
    assert plan.chunks[0].text.startswith("Chapter 1\n" + "x")
    assert "HARD_SPLIT_REQUIRED" in {item.code for item in plan.findings}
    assert all(chunk.character_count <= 60 for chunk in plan.chunks)


def test_hard_limit_does_not_split_crlf_or_combining_sequence() -> None:
    text = "Chapter 1\r\n" + "x" * 45 + "\r\n" + "e\u0301" * 40
    plan = _plan(text, 10, 30, 50)
    boundaries = {chunk.source_character_end for chunk in plan.chunks[:-1]}
    for boundary in boundaries:
        assert not (text[boundary - 1] == "\r" and text[boundary] == "\n")
        assert not unicodedata.combining(text[boundary])


def test_tail_chunk_is_merged_backward_when_within_maximum() -> None:
    text = "Chapter 1\n" + "a" * 32 + "." + "b" * 15
    plan = _plan(text, 20, 35, 60)
    assert all(chunk.character_count >= 20 for chunk in plan.chunks)


def test_unavoidable_short_chunk_has_finding_without_blocking() -> None:
    plan = _plan("Chapter 1\nTiny", 30, 40, 50)
    assert "CHUNK_BELOW_MINIMUM" in {item.code for item in plan.findings}
    assert plan.status == "ready_with_warnings"


def test_heading_longer_than_maximum_fails_closed() -> None:
    segmentation = _segmentation("Chapter 12345\nBody text without a boundary")
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(
            segmentation,
            minimum_chunk_size=5,
            target_chunk_size=10,
            maximum_chunk_size=12,
        )


def test_chunk_and_plan_fingerprints_are_exact_and_deterministic() -> None:
    text = "Chapter 1\r\n" + "Text. " * 30
    plans = [_plan(text) for _ in range(3)]
    assert plans[0] == plans[1] == plans[2]
    for chunk in plans[0].chunks:
        assert chunk.content_fingerprint == hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        assert re.fullmatch(r"[0-9a-f]{64}", chunk.content_fingerprint)
    assert re.fullmatch(r"[0-9a-f]{64}", plans[0].chunk_plan_fingerprint)
    changed_policy = PLANNER.plan(
        _segmentation(text), minimum_chunk_size=20, target_chunk_size=41, maximum_chunk_size=60
    )
    assert changed_policy.chunk_plan_fingerprint != plans[0].chunk_plan_fingerprint
    assert _plan(text + " ").source_content_fingerprint != plans[0].source_content_fingerprint
    assert _plan(text.replace("\r\n", "\n")).chunk_plan_fingerprint != plans[0].chunk_plan_fingerprint


def test_high_variance_and_excessive_count_findings_are_deterministic() -> None:
    text = "Chapter 1\n" + "a" * 950 + "\nChapter 2\nsmall"
    plan = _plan(text, 10, 900, 1100)
    assert "HIGH_CHUNK_SIZE_VARIANCE" in {item.code for item in plan.findings}
    policy = replace(DEFAULT_POLICY, excessive_chunk_count=2)
    many = BookChunkPlanner(policy).plan(
        _segmentation("Chapter 1\n" + "x" * 200),
        minimum_chunk_size=10,
        target_chunk_size=20,
        maximum_chunk_size=30,
    )
    assert "EXCESSIVE_CHUNK_COUNT" in {item.code for item in many.findings}


def test_invalid_input_and_fingerprint_mismatch_are_rejected() -> None:
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan("not a segmentation result")
    segmentation = _segmentation("Chapter 1\nText")
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(replace(segmentation, source_content_fingerprint="0" * 64))
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(replace(segmentation, segmentation_fingerprint="BAD"))


def test_segmentation_offset_gap_and_invalid_index_are_rejected() -> None:
    segmentation = _segmentation("Chapter 1\nText")
    section = segmentation.sections[0]
    shifted = replace(
        section,
        character_start=1,
        character_end=section.character_end + 1,
    )
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(replace(segmentation, sections=(shifted,)))
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(replace(segmentation, sections=(replace(section, index=1),)))


def test_nonempty_metadata_without_sections_is_rejected() -> None:
    segmentation = _segmentation("Chapter 1\nText")
    impossible = replace(
        segmentation,
        sections=(),
        source_content_fingerprint=hashlib.sha256(b"").hexdigest(),
    )
    with pytest.raises(SegmentationConsistencyError):
        PLANNER.plan(impossible)

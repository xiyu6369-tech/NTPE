from __future__ import annotations

import hashlib
import re

import pytest

from core.book_segmentation import BookStructureSegmenter
from core.book_segmentation.errors import InvalidSegmentationInputError


SEGMENTER = BookStructureSegmenter()


def _segment(text: str):
    return SEGMENTER.segment_text(text, source_name="novel.txt")


@pytest.mark.parametrize(
    "text",
    [
        "第一章\n正文",
        "第一章\n正文\n第二章\n結尾",
        "第一章\r\n正文\r\n第二章\r\n結尾\r\n",
        "  \n第一章\n文字\n\n\n第二章\n末尾  ",
        "第一章\ne\u0301與한글\n第二章\n終",
        "第一章\n無最後換行",
        "第一章\n有最後換行\n",
    ],
)
def test_content_preservation_and_offset_invariants(text: str) -> None:
    result = _segment(text)
    assert result.reconstruct_text() == text
    assert result.character_count == len(text)
    assert result.covered_character_count == len(text)
    assert result.coverage_ratio == 1.0
    assert result.sections[0].character_start == 0
    assert result.sections[-1].character_end == len(text)
    for index, section in enumerate(result.sections):
        assert section.index == index
        assert section.text == text[section.character_start:section.character_end]
        assert section.character_count == len(section.text)
        assert section.non_whitespace_character_count == sum(not c.isspace() for c in section.text)
        if index:
            assert result.sections[index - 1].character_end == section.character_start


def test_empty_text_is_a_valid_manual_review_result() -> None:
    result = _segment("")
    assert result.sections == ()
    assert result.chapter_count == 0
    assert result.status == result.action == "manual_review"
    assert result.reconstruct_text() == ""
    assert [item.code for item in result.findings] == ["EMPTY_CONTENT"]


@pytest.mark.parametrize(
    "heading",
    [
        "第一章", "第二十章", "第100章", "第一卷", "卷一", "序章", "楔子",
        "終章", "尾聲", "番外", "番外一", "後記", "附錄",
        "제1장", "제 1 장", "1장", "서장", "프롤로그", "에필로그", "외전", "후기",
        "第1章", "プロローグ", "エピローグ", "幕間", "後書き",
        "Chapter 1", "CHAPTER ONE", "Chapter One", "Prologue", "Epilogue",
        "Interlude", "Appendix", "Afterword",
    ],
)
def test_supported_heading_families_are_exactly_detected(heading: str) -> None:
    result = _segment(f"{heading}\n正文")
    assert len(result.sections) == 1
    assert result.sections[0].heading is not None
    assert result.sections[0].heading.text == heading
    assert result.sections[0].text.startswith(heading)


def test_numeric_sequence_requires_isolation_and_consecutive_structure() -> None:
    text = "1\n\n甲\n\n2\n\n乙\n\n3\n\n丙"
    result = _segment(text)
    assert result.chapter_count == 3
    assert [s.heading.text for s in result.sections if s.heading] == ["1", "2", "3"]
    assert result.reconstruct_text() == text


@pytest.mark.parametrize(
    "text",
    [
        "1\nOnly one number",
        "2026\nYear",
        "12:30\nTime",
        "1,000\nAmount",
        "1\nNo blank separator\n2\nStill body",
    ],
)
def test_unsafe_numeric_lines_are_not_detected(text: str) -> None:
    result = _segment(text)
    assert all(section.heading is None for section in result.sections)
    assert result.status == "manual_review"


def test_nonconsecutive_numeric_candidate_is_ignored_with_warning() -> None:
    result = _segment("1\n\nA\n\n2\n\nB\n\n4\n\nC")
    assert [s.heading.text for s in result.sections if s.heading] == ["1", "2"]
    assert "NUMERIC_HEADING_SEQUENCE_UNCONFIRMED" in {f.code for f in result.findings}


@pytest.mark.parametrize(
    "text",
    [
        "他讀到了第一章的最後一頁。",
        "我們將在 Chapter 2 討論這個問題。",
        "「第一章？」他反問。",
        "今天是第1章課程的第二天。",
        "房間裡有一張桌子。",
        "第1章的內容如下：這不是標題",
        "\"Chapter 1\"",
        "Chapter 2 discusses the complete sentence at length.",
        "Chapter 1 " + "x" * 100,
    ],
)
def test_false_positive_lines_do_not_create_headings(text: str) -> None:
    result = _segment(text)
    assert result.chapter_count == 0
    assert result.unclassified_count == 1


def test_front_matter_and_chapter_boundaries_preserve_all_separators() -> None:
    text = "書名\n作者\n\n第一章\n甲\n\n第二章\n乙"
    result = _segment(text)
    assert [section.section_type for section in result.sections] == ["front_matter", "chapter", "chapter"]
    assert result.sections[0].text == "書名\n作者\n\n"
    assert result.sections[1].text == "第一章\n甲\n\n"
    assert result.reconstruct_text() == text
    assert "FRONT_MATTER_PRESENT" in {item.code for item in result.findings}


def test_no_heading_preserves_whole_source_as_unclassified() -> None:
    text = "這是完整小說正文。\n沒有格式化章節。"
    result = _segment(text)
    assert len(result.sections) == 1
    assert result.sections[0].section_type == "unclassified"
    assert result.sections[0].text == text
    assert result.status == result.action == "manual_review"


def test_mixed_styles_duplicate_number_and_gap_findings() -> None:
    result = _segment("第一章\nA\nChapter 1\nB\nChapter 3\nC")
    codes = {item.code for item in result.findings}
    assert "MIXED_HEADING_STYLES" in codes
    assert "DUPLICATE_CHAPTER_NUMBER" in codes
    assert "NON_SEQUENTIAL_NUMBERING" in codes


def test_extreme_and_uneven_sections_have_findings() -> None:
    result = _segment("Chapter 1\nshort\nChapter 2\n" + "x" * 10_100)
    codes = {item.code for item in result.findings}
    assert "EXTREME_SECTION_SIZE" in codes
    assert "HIGH_SECTION_SIZE_VARIANCE" in codes


def test_source_and_segmentation_fingerprints_are_exact_and_deterministic() -> None:
    text = "Chapter 1\r\nText\r\nChapter 2\r\nMore"
    results = [_segment(text) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert results[0].source_content_fingerprint == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", results[0].segmentation_fingerprint)
    assert _segment(text + " ").source_content_fingerprint != results[0].source_content_fingerprint
    assert _segment(text.replace("\r\n", "\n")).source_content_fingerprint != results[0].source_content_fingerprint
    assert _segment(text.replace("Chapter 2", "Chapter 3")).segmentation_fingerprint != results[0].segmentation_fingerprint


def test_invalid_public_inputs_are_rejected() -> None:
    with pytest.raises(InvalidSegmentationInputError):
        SEGMENTER.segment_text(b"text", source_name="book.txt")
    with pytest.raises(InvalidSegmentationInputError):
        SEGMENTER.segment_text("text", source_name="")
    with pytest.raises(InvalidSegmentationInputError):
        SEGMENTER.segment("not an intake result")

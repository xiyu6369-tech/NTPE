from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.book_intake import BookPreflightAnalyzer, BookPreflightResult, PreflightFinding
from core.book_intake.corruption_detector import Finding, TextQualityReport
from core.book_intake.models import BookIntakeResult, LanguageDetectionResult
import core.book_intake.preflight as preflight_module


def _intake(
    text: str,
    *,
    language: str = "ko",
    status: str = "ready",
) -> BookIntakeResult:
    quality_status = {
        "ready": "clean",
        "ready_with_warnings": "warning",
        "manual_review_required": "manual_review_required",
        "blocked": "blocked",
    }[status]
    findings = () if quality_status == "clean" else (Finding("aggregate", "warning", 1, "test"),)
    quality = TextQualityReport(quality_status, findings, 100, "test", "test")
    language_result = LanguageDetectionResult(language, 95, (), "test", "test")
    return BookIntakeResult(
        source_path=Path("book.txt"),
        file_name="book.txt",
        file_size_bytes=len(text.encode("utf-8")),
        encoding="utf-8",
        encoding_confidence="high",
        text=text,
        text_length=len(text),
        quality_report=quality,
        language_result=language_result,
        status=status,
        recommended_action="test",
        summary="test",
    )


def _structured_text(blocks: int, block_length: int = 1_000) -> str:
    return "\n\n".join("가" * block_length for _ in range(blocks))


def _codes(result: BookPreflightResult) -> list[str]:
    return [finding.code for finding in result.risk_findings]


@pytest.mark.parametrize(
    ("language", "unit"),
    [
        ("ko", "한국어문장입니다"),
        ("zh", "這是一段中文內容"),
        ("ja", "これは日本語です"),
        ("en", "This is a normal English sentence"),
    ],
)
def test_normal_books_are_ready(language: str, unit: str) -> None:
    text = "\n\n".join((unit + "。") * 20 for _ in range(10))
    result = BookPreflightAnalyzer().analyze(_intake(text, language=language))
    assert result.status == "ready"
    assert result.recommended_action == "proceed"


def test_empty_content_is_blocked() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(""))
    assert result.status == "blocked"
    assert _codes(result) == ["EMPTY_CONTENT"]


def test_whitespace_only_content_is_blocked() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(" \n\t\r\n"))
    assert result.status == "blocked"
    assert "EMPTY_CONTENT" in _codes(result)


def test_very_short_book_is_warning() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 999))
    assert result.status == "ready_with_warnings"
    assert _codes(result) == ["VERY_SHORT_BOOK"]


def test_large_book_is_info_only() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(_structured_text(500)))
    assert result.status == "ready"
    assert "LARGE_BOOK" in _codes(result)


def test_very_large_book_is_warning() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(_structured_text(2_000)))
    assert result.status == "ready_with_warnings"
    assert "VERY_LARGE_BOOK" in _codes(result)


def test_extreme_book_requires_manual_review() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=20_000).analyze(
        _intake(_structured_text(10_000))
    )
    assert result.status == "manual_review_required"
    assert "EXTREME_BOOK_SIZE" in _codes(result)


@pytest.mark.parametrize(
    ("blocks", "expected", "excluded"),
    [
        (500, "LARGE_BOOK", {"VERY_LARGE_BOOK", "EXTREME_BOOK_SIZE"}),
        (2_000, "VERY_LARGE_BOOK", {"LARGE_BOOK", "EXTREME_BOOK_SIZE"}),
        (10_000, "EXTREME_BOOK_SIZE", {"LARGE_BOOK", "VERY_LARGE_BOOK"}),
    ],
)
def test_size_thresholds_supersede_lower_family(
    blocks: int, expected: str, excluded: set[str]
) -> None:
    result = BookPreflightAnalyzer(source_chunk_size=20_000).analyze(
        _intake(_structured_text(blocks))
    )
    codes = set(_codes(result))
    assert expected in codes
    assert codes.isdisjoint(excluded)


def test_excessive_line_length_is_detected() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 20_001))
    assert "EXCESSIVE_LINE_LENGTH" in _codes(result)


def test_single_line_long_book_is_detected() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 10_000))
    assert "SINGLE_LINE_BOOK" in _codes(result)


def test_low_paragraph_structure_requires_review() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 20_000))
    assert "LOW_PARAGRAPH_STRUCTURE" in _codes(result)
    assert result.status == "manual_review_required"


def test_high_blank_line_ratio_is_detected() -> None:
    text = "content\n" + "\n" * 99
    result = BookPreflightAnalyzer().analyze(_intake(text))
    assert result.line_count == 100
    assert "HIGH_BLANK_LINE_RATIO" in _codes(result)


def test_high_chunk_workload_is_detected() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=1).analyze(_intake(_structured_text(5, 1_000)))
    assert "HIGH_CHUNK_WORKLOAD" in _codes(result)


def test_extreme_chunk_workload_requires_review() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=1).analyze(_intake(_structured_text(20, 1_000)))
    assert "EXTREME_CHUNK_WORKLOAD" in _codes(result)
    assert result.status == "manual_review_required"


def test_extreme_workload_supersedes_high_workload() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=1).analyze(_intake(_structured_text(20, 1_000)))
    assert "EXTREME_CHUNK_WORKLOAD" in _codes(result)
    assert "HIGH_CHUNK_WORKLOAD" not in _codes(result)


def test_blocked_intake_remains_blocked() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(_structured_text(2), status="blocked"))
    assert result.status == "blocked"
    assert "INTAKE_BLOCKED" in _codes(result)


def test_manual_review_intake_is_not_downgraded() -> None:
    result = BookPreflightAnalyzer().analyze(
        _intake(_structured_text(2), status="manual_review_required")
    )
    assert result.status == "manual_review_required"
    assert "INTAKE_MANUAL_REVIEW" in _codes(result)


def test_warning_intake_is_preserved() -> None:
    result = BookPreflightAnalyzer().analyze(
        _intake(_structured_text(2), status="ready_with_warnings")
    )
    assert result.status == "ready_with_warnings"
    assert "INTAKE_WARNING" in _codes(result)


def test_character_counts_are_correct() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("ab 中\n"))
    assert result.character_count == 5
    assert result.non_whitespace_character_count == 3


def test_line_counts_are_correct() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("one\n\n two \nthree"))
    assert result.line_count == 4
    assert result.non_empty_line_count == 3


def test_paragraph_count_is_correct() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("one\ntwo\n\nthree\n\n\nfour"))
    assert result.paragraph_count == 3


def test_largest_and_average_line_length_are_correct() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("abc\n\n de \nxyz"))
    assert result.largest_line_length == 4
    assert result.average_line_length == 2.5


def test_empty_input_line_statistics_are_zero() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(""))
    assert result.line_count == 0
    assert result.largest_line_length == 0
    assert result.average_line_length == 0.0


def test_latin_word_estimate() -> None:
    result = BookPreflightAnalyzer().analyze(
        _intake("Hello, can't stop well-known words.", language="en")
    )
    assert result.estimated_word_count == 5


@pytest.mark.parametrize(
    ("language", "text", "expected"),
    [
        ("zh", "中文 測試。", 5),
        ("ko", "한국어 테스트", 6),
        ("ja", "日本語 テスト", 6),
    ],
)
def test_cjk_hangul_japanese_word_estimates(language: str, text: str, expected: int) -> None:
    result = BookPreflightAnalyzer().analyze(_intake(text, language=language))
    assert result.estimated_word_count == expected


def test_mixed_script_word_estimate() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("Hello 한국!", language="mixed"))
    assert result.estimated_word_count == 4


def test_default_chunk_estimate() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 1_201))
    assert result.estimated_chunk_count == 3


def test_default_token_estimate() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("가" * 101))
    assert result.estimated_source_tokens == 51


def test_custom_source_chunk_size() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=100).analyze(_intake("가" * 201))
    assert result.estimated_chunk_count == 3


def test_custom_chars_per_token() -> None:
    result = BookPreflightAnalyzer(estimated_chars_per_token=4.0).analyze(_intake("가" * 101))
    assert result.estimated_source_tokens == 26


@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_invalid_chunk_size_is_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        BookPreflightAnalyzer(source_chunk_size=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0, -0.1, True, "2"])
def test_invalid_chars_per_token_is_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        BookPreflightAnalyzer(estimated_chars_per_token=value)  # type: ignore[arg-type]


def test_book_preflight_result_is_immutable() -> None:
    result = BookPreflightAnalyzer().analyze(_intake(_structured_text(2)))
    with pytest.raises(FrozenInstanceError):
        result.status = "blocked"


def test_preflight_finding_is_immutable() -> None:
    finding = BookPreflightAnalyzer().analyze(_intake("short")).risk_findings[0]
    with pytest.raises(FrozenInstanceError):
        finding.code = "OTHER"


def test_risk_findings_is_tuple() -> None:
    result = BookPreflightAnalyzer().analyze(_intake("short"))
    assert isinstance(result.risk_findings, tuple)
    assert isinstance(result.risk_findings[0], PreflightFinding)


def test_repeated_analysis_is_deterministic() -> None:
    intake = _intake(_structured_text(2))
    analyzer = BookPreflightAnalyzer()
    assert analyzer.analyze(intake) == analyzer.analyze(intake)


def test_input_result_remains_unchanged() -> None:
    intake = _intake(_structured_text(2))
    before = repr(intake)
    BookPreflightAnalyzer().analyze(intake)
    assert repr(intake) == before


def test_analyzer_does_not_read_source_file(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("source file read attempted")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "read_bytes", fail)
    assert BookPreflightAnalyzer().analyze(_intake(_structured_text(2))).status == "ready"


def test_analyzer_does_not_write_files(tmp_path: Path) -> None:
    before = tuple(tmp_path.iterdir())
    BookPreflightAnalyzer().analyze(_intake(_structured_text(2)))
    assert tuple(tmp_path.iterdir()) == before


def test_module_has_no_provider_or_network_dependency() -> None:
    source = inspect.getsource(preflight_module).lower()
    assert "provider" not in source
    assert "requests" not in source
    assert "urllib" not in source


def test_finding_order_is_explicit_and_deterministic() -> None:
    result = BookPreflightAnalyzer(source_chunk_size=1).analyze(
        _intake("가" * 20_001, status="blocked")
    )
    assert _codes(result) == [
        "EXCESSIVE_LINE_LENGTH",
        "SINGLE_LINE_BOOK",
        "LOW_PARAGRAPH_STRUCTURE",
        "EXTREME_CHUNK_WORKLOAD",
        "INTAKE_BLOCKED",
    ]


def test_summary_contains_no_source_text_or_timestamp() -> None:
    secret = "UNIQUE_NOVEL_SENTENCE"
    result = BookPreflightAnalyzer().analyze(_intake((secret + " ") * 100))
    assert secret not in result.summary
    assert "202" not in result.summary

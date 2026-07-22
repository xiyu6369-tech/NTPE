from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .models import BookIntakeResult, BookPreflightResult, PreflightFinding


@dataclass(frozen=True, slots=True)
class _PreflightPolicy:
    very_short_characters: int = 1_000
    large_book_characters: int = 500_000
    very_large_book_characters: int = 2_000_000
    extreme_book_characters: int = 10_000_000
    excessive_line_length: int = 20_000
    single_line_book_characters: int = 10_000
    low_structure_characters: int = 20_000
    low_structure_paragraphs: int = 1
    blank_ratio_minimum_lines: int = 100
    blank_ratio_threshold: float = 0.20
    high_chunk_workload: int = 5_000
    extreme_chunk_workload: int = 20_000


_POLICY = _PreflightPolicy()
_LATIN_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")

class BookPreflightAnalyzer:
    """Analyze intake text offline; average line length is rounded to two decimals."""

    def __init__(
        self,
        source_chunk_size: int = 600,
        estimated_chars_per_token: float = 2.0,
    ) -> None:
        if isinstance(source_chunk_size, bool) or not isinstance(source_chunk_size, int):
            raise TypeError("source_chunk_size must be a positive integer")
        if source_chunk_size <= 0:
            raise ValueError("source_chunk_size must be a positive integer")
        if isinstance(estimated_chars_per_token, bool) or not isinstance(
            estimated_chars_per_token, (int, float)
        ):
            raise TypeError("estimated_chars_per_token must be greater than zero")
        if not math.isfinite(float(estimated_chars_per_token)) or estimated_chars_per_token <= 0:
            raise ValueError("estimated_chars_per_token must be greater than zero")
        self._source_chunk_size = source_chunk_size
        self._estimated_chars_per_token = float(estimated_chars_per_token)

    def analyze(self, intake_result: BookIntakeResult) -> BookPreflightResult:
        """Return book-scale statistics without rereading or mutating the source."""
        text = intake_result.text
        lines = text.splitlines() if text else []
        character_count = len(text)
        non_whitespace_count = sum(not character.isspace() for character in text)
        line_count = len(lines)
        non_empty_line_count = sum(bool(line.strip()) for line in lines)
        paragraph_count = _count_paragraphs(lines)
        largest_line_length = max((len(line) for line in lines), default=0)
        average_line_length = (
            round(sum(len(line) for line in lines) / line_count, 2) if line_count else 0.0
        )
        estimated_word_count = _estimate_words(text, intake_result.language_result.language)
        estimated_chunk_count = (
            math.ceil(non_whitespace_count / self._source_chunk_size)
            if non_whitespace_count
            else 0
        )
        estimated_source_tokens = (
            math.ceil(non_whitespace_count / self._estimated_chars_per_token)
            if non_whitespace_count
            else 0
        )
        findings = _build_findings(
            intake_result=intake_result,
            character_count=character_count,
            non_whitespace_count=non_whitespace_count,
            line_count=line_count,
            non_empty_line_count=non_empty_line_count,
            paragraph_count=paragraph_count,
            largest_line_length=largest_line_length,
            estimated_chunk_count=estimated_chunk_count,
        )
        status = _resolve_status(findings)
        return BookPreflightResult(
            source_path=intake_result.source_path,
            file_name=intake_result.file_name,
            source_language=intake_result.language_result.language,
            encoding=intake_result.encoding,
            character_count=character_count,
            non_whitespace_character_count=non_whitespace_count,
            line_count=line_count,
            non_empty_line_count=non_empty_line_count,
            paragraph_count=paragraph_count,
            estimated_word_count=estimated_word_count,
            estimated_chunk_count=estimated_chunk_count,
            estimated_source_tokens=estimated_source_tokens,
            largest_line_length=largest_line_length,
            average_line_length=average_line_length,
            risk_findings=findings,
            status=status,
            recommended_action=_recommended_action(status),
            summary=_build_summary(status, findings, character_count, estimated_chunk_count),
        )


def _count_paragraphs(lines: list[str]) -> int:
    paragraphs = 0
    inside_paragraph = False
    for line in lines:
        if line.strip():
            if not inside_paragraph:
                paragraphs += 1
                inside_paragraph = True
        else:
            inside_paragraph = False
    return paragraphs


def _estimate_words(text: str, language: str) -> int:
    if language == "en":
        return len(_LATIN_WORD_PATTERN.findall(text))
    if language == "mixed":
        latin_words = len(_LATIN_WORD_PATTERN.findall(text))
        non_latin_characters = sum(
            not character.isspace() and not _is_latin_letter(character) for character in text
        )
        return latin_words + non_latin_characters
    return sum(not character.isspace() for character in text)


def _is_latin_letter(character: str) -> bool:
    return "A" <= character <= "Z" or "a" <= character <= "z"


def _finding(
    code: str,
    severity: str,
    message: str,
    observed_value: int | float | str,
    threshold: int | float | str,
) -> PreflightFinding:
    return PreflightFinding(code, severity, message, observed_value, threshold)


def _build_findings(
    *,
    intake_result: BookIntakeResult,
    character_count: int,
    non_whitespace_count: int,
    line_count: int,
    non_empty_line_count: int,
    paragraph_count: int,
    largest_line_length: int,
    estimated_chunk_count: int,
) -> tuple[PreflightFinding, ...]:
    findings: list[PreflightFinding] = []

    if non_whitespace_count == 0:
        findings.append(_finding("EMPTY_CONTENT", "blocking", "No non-whitespace content.", 0, 1))
    elif non_whitespace_count < _POLICY.very_short_characters:
        findings.append(
            _finding(
                "VERY_SHORT_BOOK",
                "warning",
                "Book content is below the normal long-form threshold.",
                non_whitespace_count,
                _POLICY.very_short_characters,
            )
        )

    if character_count >= _POLICY.extreme_book_characters:
        findings.append(
            _finding(
                "EXTREME_BOOK_SIZE",
                "manual_review",
                "Book size requires manual review.",
                character_count,
                _POLICY.extreme_book_characters,
            )
        )
    elif character_count >= _POLICY.very_large_book_characters:
        findings.append(
            _finding(
                "VERY_LARGE_BOOK",
                "warning",
                "Book is very large.",
                character_count,
                _POLICY.very_large_book_characters,
            )
        )
    elif character_count >= _POLICY.large_book_characters:
        findings.append(
            _finding(
                "LARGE_BOOK",
                "info",
                "Book is large.",
                character_count,
                _POLICY.large_book_characters,
            )
        )

    if largest_line_length > _POLICY.excessive_line_length:
        findings.append(
            _finding(
                "EXCESSIVE_LINE_LENGTH",
                "warning",
                "At least one logical line is excessively long.",
                largest_line_length,
                _POLICY.excessive_line_length,
            )
        )
    if line_count == 1 and character_count >= _POLICY.single_line_book_characters:
        findings.append(
            _finding(
                "SINGLE_LINE_BOOK",
                "warning",
                "Long-form content is stored as one logical line.",
                line_count,
                _POLICY.single_line_book_characters,
            )
        )
    if (
        character_count >= _POLICY.low_structure_characters
        and paragraph_count <= _POLICY.low_structure_paragraphs
    ):
        findings.append(
            _finding(
                "LOW_PARAGRAPH_STRUCTURE",
                "manual_review",
                "Long-form content has insufficient paragraph structure.",
                paragraph_count,
                _POLICY.low_structure_paragraphs,
            )
        )
    if line_count >= _POLICY.blank_ratio_minimum_lines:
        non_empty_ratio = non_empty_line_count / line_count
        if non_empty_ratio < _POLICY.blank_ratio_threshold:
            findings.append(
                _finding(
                    "HIGH_BLANK_LINE_RATIO",
                    "warning",
                    "Most logical lines are blank.",
                    round(non_empty_ratio, 4),
                    _POLICY.blank_ratio_threshold,
                )
            )

    if estimated_chunk_count >= _POLICY.extreme_chunk_workload:
        findings.append(
            _finding(
                "EXTREME_CHUNK_WORKLOAD",
                "manual_review",
                "Estimated chunk workload requires manual review.",
                estimated_chunk_count,
                _POLICY.extreme_chunk_workload,
            )
        )
    elif estimated_chunk_count >= _POLICY.high_chunk_workload:
        findings.append(
            _finding(
                "HIGH_CHUNK_WORKLOAD",
                "warning",
                "Estimated chunk workload is high.",
                estimated_chunk_count,
                _POLICY.high_chunk_workload,
            )
        )

    if intake_result.status == "blocked":
        findings.append(
            _finding(
                "INTAKE_BLOCKED",
                "blocking",
                "The Book Intake result is blocked.",
                intake_result.status,
                "ready",
            )
        )
    elif intake_result.status == "manual_review_required":
        findings.append(
            _finding(
                "INTAKE_MANUAL_REVIEW",
                "manual_review",
                "The Book Intake result requires manual review.",
                intake_result.status,
                "ready",
            )
        )
    elif intake_result.status == "ready_with_warnings":
        findings.append(
            _finding(
                "INTAKE_WARNING",
                "warning",
                "The Book Intake result contains warnings.",
                intake_result.status,
                "ready",
            )
        )

    return tuple(findings)


def _resolve_status(findings: tuple[PreflightFinding, ...]) -> str:
    severities = {finding.severity for finding in findings}
    if "blocking" in severities:
        return "blocked"
    if "manual_review" in severities:
        return "manual_review_required"
    if "warning" in severities:
        return "ready_with_warnings"
    return "ready"


def _recommended_action(status: str) -> str:
    if status == "ready":
        return "proceed"
    if status == "ready_with_warnings":
        return "proceed_with_warning"
    if status == "manual_review_required":
        return "manual_review"
    return "reject"


def _build_summary(
    status: str,
    findings: tuple[PreflightFinding, ...],
    character_count: int,
    estimated_chunk_count: int,
) -> str:
    codes = {finding.code for finding in findings}
    if "INTAKE_BLOCKED" in codes:
        return "Preflight blocked because the intake result is blocked."
    if status == "blocked":
        return "Preflight blocked because the book contains no processable content."
    if "EXTREME_BOOK_SIZE" in codes:
        return "Preflight requires manual review due to extreme book size."
    if status == "manual_review_required":
        return (
            f"Preflight requires manual review. {character_count:,} characters, "
            f"{estimated_chunk_count:,} estimated chunks."
        )
    if status == "ready_with_warnings":
        return (
            f"Preflight completed. {character_count:,} characters, "
            f"{estimated_chunk_count:,} estimated chunks. Ready with warnings."
        )
    return (
        f"Preflight completed. {character_count:,} characters, "
        f"{estimated_chunk_count:,} estimated chunks. Ready for processing."
    )
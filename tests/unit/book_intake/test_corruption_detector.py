from __future__ import annotations

import pytest

from core.book_intake.corruption_detector import (
    Finding,
    TextCorruptionDetector,
    TextQualityReport,
)


# =============================================================================
# Helper
# =============================================================================

def _make_report(text: str) -> TextQualityReport:
    return TextCorruptionDetector().analyze(text)


# =============================================================================
# Tests — Clean
# =============================================================================

class TestClean:
    def test_ascii_clean(self) -> None:
        report = _make_report("Hello, world! This is normal text.")
        assert report.status == "clean"
        assert report.score == 100
        assert report.recommended_action == "accept"
        assert len(report.findings) == 0

    def test_unicode_normal_text(self) -> None:
        report = _make_report("Hello — normal em dash and curly quotes \u2018\u2019 \u201C\u201D.")
        assert report.status == "clean"
        assert report.score == 100

    def test_korean_text(self) -> None:
        text = "한국어 텍스트는 정상적으로 분석되어야 합니다. 안녕하세요."
        report = _make_report(text)
        assert report.status == "clean"
        assert report.score == 100
        assert report.summary == "No corruption detected."

    def test_chinese_text(self) -> None:
        text = "繁體中文文本應該正常通過檢測。這是一段測試文字。"
        report = _make_report(text)
        assert report.status == "clean"
        assert report.score == 100

    def test_japanese_text(self) -> None:
        text = "日本語のテキストも正常に検出されるべきです。こんにちは。"
        report = _make_report(text)
        assert report.status == "clean"
        assert report.score == 100


# =============================================================================
# Tests — Replacement
# =============================================================================

class TestReplacement:
    def test_single_replacement(self) -> None:
        text = "Hello\uFFFD world"
        report = _make_report(text)
        assert report.status == "warning"
        assert report.score < 100
        findings = {f.code: f for f in report.findings}
        assert "replacement_character" in findings
        f = findings["replacement_character"]
        assert f.severity == "warning"
        assert f.count == 1

    def test_multiple_replacements(self) -> None:
        text = "\uFFFD\uFFFD\uFFFD bad encoding \uFFFD\uFFFD"
        report = _make_report(text)
        assert report.status == "warning"
        f = [f for f in report.findings if f.code == "replacement_character"][0]
        assert f.count == 5

    def test_no_replacement_in_clean_text(self) -> None:
        report = _make_report("No replacement here.")
        for f in report.findings:
            assert f.code != "replacement_character"


# =============================================================================
# Tests — NULL
# =============================================================================

class TestNull:
    def test_null_characters(self) -> None:
        text = "hello\x00world\x00"
        report = _make_report(text)
        assert report.status in ("blocked", "manual_review_required")
        findings = {f.code: f for f in report.findings}
        assert "null_character" in findings
        f = findings["null_character"]
        assert f.severity == "error"
        assert f.count == 2

    def test_no_null(self) -> None:
        report = _make_report("normal text\nwith newline")
        for f in report.findings:
            assert f.code != "null_character"


# =============================================================================
# Tests — Control Character
# =============================================================================

class TestControlCharacter:
    def test_control_characters(self) -> None:
        # \x01 (SOH), \x02 (STX), \x03 (ETX) — non-printable control chars
        text = "start\x01\x02\x03end"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "control_character" in findings
        f = findings["control_character"]
        assert f.count == 3
        # 3 chars ≤ 10 → warning
        assert f.severity == "warning"

    def test_many_control_characters(self) -> None:
        text = "\x01" * 15 + "data"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        f = findings["control_character"]
        assert f.count == 15
        assert f.severity == "error"

    def test_allowed_control_not_flagged(self) -> None:
        text = "Line1\nLine2\r\n\tIndented"
        report = _make_report(text)
        for f in report.findings:
            assert f.code != "control_character"


# =============================================================================
# Tests — Mojibake
# =============================================================================

class TestMojibake:
    def test_single_mojibake_indicator(self) -> None:
        # Single Ã (common UTF-8 misdecode indicator)
        text = "Hello \u00C3 world"
        report = _make_report(text)
        # 1 char → warning or clean depending on clustering
        findings = {f.code: f for f in report.findings}
        assert "mojibake_pattern" in findings
        f = findings["mojibake_pattern"]
        assert f.severity == "warning"

    def test_clustered_mojibake(self) -> None:
        # Multiple sequential Ã symbols — strong mojibake signal
        text = "text \u00C3\u00C3\u00C3 more text"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        f = findings["mojibake_pattern"]
        assert f.severity == "error"

    def test_mixed_mojibake_chars(self) -> None:
        text = "\u00C3\u00C2\u00A4\uFFE6 data"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "mojibake_pattern" in findings

    def test_no_mojibake_in_normal_cjk(self) -> None:
        report = _make_report("한국어 中文 日本語")
        for f in report.findings:
            assert f.code != "mojibake_pattern"


# =============================================================================
# Tests — Private Use
# =============================================================================

class TestPrivateUse:
    def test_private_use_area(self) -> None:
        # U+E000 is the start of BMP PUA
        text = "data \uE000\uE001 private"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "private_use_area" in findings
        f = findings["private_use_area"]
        assert f.count == 2
        assert f.severity == "warning"  # ≤ 100

    def test_many_pua_chars(self) -> None:
        text = "\uE000" * 120 + "data"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        f = findings["private_use_area"]
        assert f.severity == "error"


# =============================================================================
# Tests — Noncharacter
# =============================================================================

class TestNoncharacter:
    def test_noncharacters(self) -> None:
        # U+FFFF is a noncharacter
        text = "data \uFFFF here"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "noncharacter" in findings
        f = findings["noncharacter"]
        assert f.severity == "error"
        assert f.count == 1

    def test_fdd0_noncharacter(self) -> None:
        text = "\uFDD0 test"
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "noncharacter" in findings
        f = findings["noncharacter"]
        assert f.count == 1


# =============================================================================
# Tests — Long Line
# =============================================================================

class TestLongLine:
    def test_line_under_threshold(self) -> None:
        text = "a" * 15000  # under 20000
        report = _make_report(text)
        for f in report.findings:
            assert f.code != "long_line"

    def test_line_over_threshold(self) -> None:
        text = "x" * 25000  # > 20000
        report = _make_report(text)
        findings = {f.code: f for f in report.findings}
        assert "long_line" in findings
        f = findings["long_line"]
        assert f.count == 1
        assert f.severity == "warning"


# =============================================================================
# Tests — Multiple Findings
# =============================================================================

class TestMultipleFindings:
    def test_multiple_issues(self) -> None:
        # Replacement + NULL + control → at least 3 findings with ≥1 error
        text = "\uFFFD hello \x00 world \x01\x02"
        report = _make_report(text)
        assert len(report.findings) >= 3
        # ≥1 error + ≥3 findings → blocked
        assert report.status == "blocked"
        assert report.score < 80


# =============================================================================
# Tests — Empty String
# =============================================================================

class TestEmptyString:
    def test_empty(self) -> None:
        report = _make_report("")
        assert report.status == "clean"
        assert report.score == 100
        assert report.recommended_action == "accept"
        assert len(report.findings) == 0
        assert report.summary == "Empty input; no corruption detected."


# =============================================================================
# Tests — Immutable Model
# =============================================================================

class TestImmutableModel:
    def test_finding_is_immutable(self) -> None:
        f = Finding(code="test", severity="warn", count=1, message="msg")
        with pytest.raises(AttributeError):
            f.code = "changed"  # type: ignore[misc]

    def test_report_is_immutable(self) -> None:
        r = TextQualityReport(
            status="clean", findings=(), score=100, recommended_action="accept", summary="ok"
        )
        with pytest.raises(AttributeError):
            r.status = "blocked"  # type: ignore[misc]

    def test_finding_equality(self) -> None:
        f1 = Finding(code="x", severity="w", count=1, message="m")
        f2 = Finding(code="x", severity="w", count=1, message="m")
        assert f1 == f2
        assert hash(f1) == hash(f2)


# =============================================================================
# Tests — Score and Status Logic
# =============================================================================

class TestScoreLogic:
    def test_perfect_score_for_clean_text(self) -> None:
        report = _make_report("Normal text with no issues at all.")
        assert report.score == 100

    def test_score_reduction_for_warnings(self) -> None:
        # 5 replacements → score reduction
        text = "\uFFFD" * 5
        report = _make_report(text)
        assert report.score < 100

    def test_score_never_below_zero(self) -> None:
        # Extreme corruption
        text = "\x00" * 200 + "\uFFFF" * 50 + "\uFFFD" * 100
        report = _make_report(text)
        assert report.score >= 0


# =============================================================================
# Tests — Summary
# =============================================================================

class TestSummary:
    def test_clean_summary(self) -> None:
        report = _make_report("Normal.")
        assert report.summary == "No corruption detected."

    def test_single_issue_summary(self) -> None:
        text = "\uFFFD"
        report = _make_report(text)
        assert "replacement" in report.summary.lower()

    def test_multiple_issue_condensed_summary(self) -> None:
        text = "\uFFFD \x00 \uFFFF" + "\x01" * 20
        report = _make_report(text)
        assert "Multiple issues detected" in report.summary
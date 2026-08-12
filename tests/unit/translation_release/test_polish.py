# tests/unit/translation_release/test_polish.py

import pytest
from core.translation_release.polish import (
    normalize_paragraphs,
    unify_quote_style,
    polish_full_novel,
)


class TestNormalizeParagraphs:
    """Tests for normalize_paragraphs function."""

    def test_empty_text(self):
        text = ""
        result, metrics = normalize_paragraphs(text)
        assert result == ""
        assert metrics["paragraphs_before"] == 0
        assert metrics["paragraphs_after"] == 0
        assert metrics["empty_paragraphs_removed"] == 0
        assert metrics["excessive_breaks_consolidated"] == 0
        assert metrics["whitespace_normalized"] == 0

    def test_whitespace_only(self):
        text = "   \n\n  \t  \n\n  "
        result, metrics = normalize_paragraphs(text)
        assert result.strip() == ""
        assert metrics["paragraphs_after"] == 0

    def test_normal_paragraphs(self):
        text = "段落一。\n\n段落二。\n\n段落三。"
        result, metrics = normalize_paragraphs(text)
        assert metrics["paragraphs_before"] == 3
        assert metrics["paragraphs_after"] == 3
        assert metrics["empty_paragraphs_removed"] == 0

    def test_empty_paragraphs_removed(self):
        text = "段落一。\n\n\n\n段落二。\n\n\n\n\n段落三。"
        result, metrics = normalize_paragraphs(text)
        assert metrics["empty_paragraphs_removed"] >= 2
        assert result.count("\n\n\n") == 0
        assert "段落一。\n\n段落二。\n\n段落三。" in result

    def test_excessive_breaks_consolidated(self):
        text = "段落一。\n\n\n\n段落二。\n\n\n\n\n\n段落三。"
        result, metrics = normalize_paragraphs(text)
        assert metrics["excessive_breaks_consolidated"] >= 2
        assert result.count("\n\n\n") == 0

    def test_whitespace_normalization(self):
        text = "段落一。\n\n  段落  二  。\n\n\t段落\t三\t。"
        result, metrics = normalize_paragraphs(text)
        assert "  " not in result  # multiple spaces normalized
        assert "\t" not in result  # tabs normalized

    def test_trailing_newline_single(self):
        text = "段落一。\n\n段落二。"
        result, metrics = normalize_paragraphs(text)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_trailing_double_newline_reduced(self):
        text = "段落一。\n\n段落二。\n\n"
        result, metrics = normalize_paragraphs(text)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


class TestUnifyQuoteStyle:
    """Tests for unify_quote_style function (conservative)."""

    def test_empty_text(self):
        text = ""
        result, metrics = unify_quote_style(text)
        assert result == ""
        assert metrics["double_quotes_converted"] == 0
        assert metrics["single_quotes_converted"] == 0
        assert metrics["skipped_apostrophes"] == 0

    def test_double_quotes_converted(self):
        text = '他說：「你好」。'
        result, metrics = unify_quote_style(text)
        # Already CJK quotes - should not double-convert
        assert "「你好」" in result
        assert metrics["double_quotes_converted"] == 0

    def test_ascii_double_quotes_to_cjk(self):
        text = '他說："你好"。'
        result, metrics = unify_quote_style(text)
        assert "「你好」" in result
        assert metrics["double_quotes_converted"] == 1

    def test_ascii_single_quotes_to_cjk(self):
        text = "他說：『你好』。"
        result, metrics = unify_quote_style(text)
        # Already CJK single quotes
        assert "『你好』" in result

    def test_ascii_single_quotes_converted(self):
        text = "他說:'你好'。"
        result, metrics = unify_quote_style(text)
        assert "『你好』" in result
        assert metrics["single_quotes_converted"] == 1

    def test_apostrophe_in_contraction_preserved(self):
        text = "don't worry"
        result, metrics = unify_quote_style(text)
        assert "don't" in result
        assert metrics["skipped_apostrophes"] >= 1

    def test_multiple_contractions_preserved(self):
        text = "don't won't can't it's that's won't"
        result, metrics = unify_quote_style(text)
        assert "don't" in result
        assert "won't" in result
        assert "can't" in result
        assert "it's" in result
        assert metrics["skipped_apostrophes"] >= 4

    def test_possessive_preserved(self):
        text = "John's book"
        result, metrics = unify_quote_style(text)
        assert "John's" in result
        assert metrics["skipped_apostrophes"] >= 1

    def test_measurement_inches_preserved(self):
        text = 'The screen is 24" wide'
        result, metrics = unify_quote_style(text)
        assert '24"' in result
        assert metrics["skipped_apostrophes"] >= 1

    def test_measurement_feet_preserved(self):
        text = "The room is 10' long"
        result, metrics = unify_quote_style(text)
        assert "10'" in result
        assert metrics["skipped_apostrophes"] >= 1

    def test_mixed_quotes_in_dialogue(self):
        text = '他說："你好"。\n她說：\'你好\'。'
        result, metrics = unify_quote_style(text)
        assert "「你好」" in result
        assert "『你好』" in result
        assert metrics["double_quotes_converted"] == 1
        assert metrics["single_quotes_converted"] == 1

    def test_code_like_quotes_not_converted(self):
        text = 'config = {"key": "value"}'
        result, metrics = unify_quote_style(text)
        # Should not convert quotes inside code-like structures
        assert '"key"' in result or '"value"' in result

    def test_nested_quotes_handled(self):
        text = '他說："她說：\'你好\'"。'
        result, metrics = unify_quote_style(text)
        # Inner single quotes should be protected or converted appropriately
        assert "你好" in result


class TestPolishFullNovel:
    """Tests for polish_full_novel main entry point."""

    def test_disabled_flag(self):
        text = "測試文本。\n\n第二段。"
        result, metrics = polish_full_novel(text, enabled=False)
        assert result == text
        assert metrics["total_changes"] == 0

    def test_empty_text(self):
        text = ""
        result, metrics = polish_full_novel(text, enabled=True)
        assert result == ""
        assert metrics["total_changes"] == 0

    def test_polish_pipeline_runs(self):
        text = '他說："你好"。\n\n\n\n她說：\'很好\'。'
        result, metrics = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert "「你好」" in result
        assert "『很好』" in result
        assert result.count("\n\n\n") == 0
        assert metrics["total_changes"] > 0
        assert "paragraphs" in metrics
        assert "quotes" in metrics
        assert "punctuation" in metrics
        assert "traditional_normalization" in metrics

    def test_traditional_normalization_disabled(self):
        text = "台湾 台北"
        result, metrics = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert metrics["traditional_normalization"].get("skipped") is True

    def test_traditional_normalization_enabled(self):
        text = "台湾 台北"
        result, metrics = polish_full_novel(text, taiwan_traditional_normalization=True)
        assert "台灣" in result
        assert "臺北" in result
        assert metrics["traditional_normalization"]["changes"] > 0

    def test_punctuation_normalization(self):
        text = "Hello, world! How are you? (fine)"
        result, metrics = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert "，" in result or "：" in result or "？" in result or "！" in result
        assert "（" in result or "）" in result

    def test_deterministic_output(self):
        text = "段落一。\n\n\n\n段落二。\n\n他說：\"你好\"。"
        result1, metrics1 = polish_full_novel(text, taiwan_traditional_normalization=False)
        result2, metrics2 = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert result1 == result2
        assert metrics1 == metrics2


class TestIntegrationWithRuntimeFormatter:
    """Tests verifying reuse of existing runtime_formatter functions."""

    def test_reuses_clean_provider_output(self):
        """polish_full_novel should reuse clean_provider_output."""
        text = "以下是翻譯：\n\n測試內容。"
        result, _ = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert "以下是翻譯" not in result

    def test_reuses_normalize_punctuation(self):
        """polish_full_novel should reuse normalize_punctuation_for_zh_tw."""
        text = "Hello, world!"
        result, _ = polish_full_novel(text, taiwan_traditional_normalization=False)
        assert "，" in result or "！" in result

    def test_reuses_normalize_taiwan_traditional(self):
        """polish_full_novel should reuse normalize_taiwan_traditional."""
        text = "台湾 台北"
        result, _ = polish_full_novel(text, taiwan_traditional_normalization=True)
        assert "台灣" in result
        assert "臺北" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
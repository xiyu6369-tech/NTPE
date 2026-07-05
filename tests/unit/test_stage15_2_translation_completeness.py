from core.quality import (
    QualityContext,
    TranslationCompletenessAnalyzer,
    TranslationQualityEngine,
)
from core.quality.completeness_report import CompletenessReport


def test_completeness_analyzer_detects_missing_segment():
    source = "첫 번째 문장입니다.\n\n두 번째 문장입니다.\n\n세 번째 문장입니다."
    translated = "第一句。\n\n第二句。"
    analysis = TranslationCompletenessAnalyzer().analyze(source, translated)
    assert analysis.source_segments == 3
    assert analysis.translated_segments == 2
    assert len(analysis.missing_segments) == 1
    assert analysis.missing_segments[0].index == 3
    assert not analysis.passed


def test_completeness_analyzer_detects_short_segment():
    source = "이것은 매우 긴 원문 문단이며 인물의 행동과 감정 설명이 길게 이어지는 중요한 장면입니다."
    translated = "短句。"
    analysis = TranslationCompletenessAnalyzer().analyze(source, translated)
    assert analysis.short_segments
    assert analysis.short_segments[0].status in {"too_short", "possibly_short"}


def test_quality_engine_includes_completeness_rules():
    source = "첫 번째 문장입니다.\n\n두 번째 문장입니다.\n\n세 번째 문장입니다."
    translated = "第一句。\n\n第二句。"
    result = TranslationQualityEngine().evaluate(QualityContext(source_text=source, translated_text=translated))
    names = [issue.rule_name for issue in result.issues]
    assert "missing_segment_detection" in names
    assert result.status.value in {"WARNING", "FAIL"}


def test_completeness_report_serializes_summary():
    analysis = TranslationCompletenessAnalyzer().analyze("A.\n\nB.", "甲。")
    report = CompletenessReport(analysis)
    data = report.to_dict()
    assert data["stage"] == "Stage-15.2"
    assert "NTPE Completeness Report" in report.to_summary_text()

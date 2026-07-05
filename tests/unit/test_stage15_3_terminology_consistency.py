from core.quality import QualityContext, TranslationQualityEngine
from core.quality.terminology_consistency import (
    TerminologyConsistencyAnalyzer,
    TerminologyEntry,
    build_default_character_glossary,
)
from core.quality.terminology_report import TerminologyReport


def test_terminology_analyzer_detects_missing_canonical_translation():
    analyzer = TerminologyConsistencyAnalyzer([
        TerminologyEntry(source="정태의", canonical="鄭泰義", aliases=("正太義",), category="character")
    ])
    analysis = analyzer.analyze("정태의는 말했다. 정태의는 웃었다.", "他說了。正太義笑了。")
    assert analysis.entries_checked == 1
    assert analysis.warning_count == 1
    assert analysis.error_count == 0
    assert analysis.issues[0].issue_type == "alias_or_drift_detected"


def test_terminology_analyzer_detects_missing_term():
    analyzer = TerminologyConsistencyAnalyzer.from_glossary({"일라이": "伊萊"})
    analysis = analyzer.analyze("일라이가 방에 들어왔다.", "那個男人走進房間。")
    assert not analysis.passed
    assert analysis.error_count == 1
    assert analysis.issues[0].issue_type == "missing_canonical_translation"


def test_quality_engine_uses_context_glossary_metadata():
    context = QualityContext(
        source_text="카일은 정태의에게 말했다.",
        translated_text="卡爾對正太義說。",
        metadata={
            "glossary": {
                "카일": {"canonical": "凱爾", "aliases": ["卡爾"], "category": "character"},
                "정태의": {"canonical": "鄭泰義", "aliases": ["正太義"], "category": "character"},
            }
        },
    )
    result = TranslationQualityEngine().evaluate(context)
    assert any(issue.rule_name == "terminology_character_consistency" for issue in result.issues)
    assert result.status.value in {"WARNING", "FAIL"}


def test_terminology_report_outputs_text_and_json():
    analysis = TerminologyConsistencyAnalyzer.from_glossary(build_default_character_glossary()).analyze(
        "정태의와 일라이가 있었다.",
        "鄭泰義和伊萊在那裡。",
    )
    report = TerminologyReport(analysis)
    assert "Terminology" in report.to_text()
    assert "entries_checked" in report.to_json()

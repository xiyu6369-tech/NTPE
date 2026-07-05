# =====================================================
# NTPE 1.2 Professional
# Stage-15.5 Formatting / Structure Integrity Engine Tests
# =====================================================

from core.quality.quality_context import QualityContext
from core.quality.quality_result import QualityStatus
from core.quality.quality_rules import build_default_quality_rules
from core.quality.structure_integrity import StructureIntegrityAnalyzer
from core.quality.structure_report import StructureIntegrityReport
from core.quality.structure_rules import StructureIntegrityRule


def test_unbalanced_dialogue_delimiter_detection():
    analysis = StructureIntegrityAnalyzer().analyze("그가 말했다.", "「他說。")
    assert any(issue.issue_type == "unbalanced_delimiter" for issue in analysis.issues)
    assert not analysis.passed


def test_missing_placeholder_detection():
    source = "Hello {name}, chapter <KEEP>."
    target = "你好，章節。"
    analysis = StructureIntegrityAnalyzer().analyze(source, target)
    assert any(issue.issue_type == "missing_placeholder" for issue in analysis.issues)


def test_paragraph_count_drift_detection():
    source = "A\n\nB\n\nC\n\nD"
    target = "甲乙丙丁"
    analysis = StructureIntegrityAnalyzer().analyze(source, target)
    assert any(issue.issue_type == "paragraph_count_drift" for issue in analysis.issues)


def test_structure_rule_integrates_with_quality_result():
    context = QualityContext(source_text="A {x}", translated_text="「甲")
    result = StructureIntegrityRule().evaluate(context)
    assert result.issues
    assert "structure_integrity" in result.metrics
    assert result.status in {QualityStatus.WARNING, QualityStatus.FAIL}


def test_structure_report_outputs_summary():
    analysis = StructureIntegrityAnalyzer().analyze("第1章\n\nA", "第一章\n\n甲")
    summary = StructureIntegrityReport(analysis).to_summary_text()
    assert "Stage-15.5" in summary
    assert "Structure score" in summary


def test_default_quality_rules_include_structure_integrity_rule():
    names = [rule.name for rule in build_default_quality_rules()]
    assert "formatting_structure_integrity" in names

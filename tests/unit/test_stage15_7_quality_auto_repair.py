# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer Tests
# =====================================================

from core.quality import (
    QualityAutoRepairEngine,
    QualityContext,
    QualityRepairPolicy,
    QualityRepairReport,
    RepairStatus,
    TranslationQualityEngine,
    repair_translation_text,
)


def test_auto_repair_collapses_duplicate_lines_and_whitespace():
    context = QualityContext(
        source_text="안녕 {name}",
        translated_text="你好 {name}   \r\n你好 {name}   \r\n\r\n\r\n\r\n下一段",
    )
    result = QualityAutoRepairEngine().repair(context)
    assert result.status == RepairStatus.REPAIRED
    assert "\r" not in result.repaired_text
    assert result.repaired_text.count("你好 {name}") == 1
    assert len(result.actions) >= 2


def test_auto_repair_applies_explicit_glossary():
    policy = QualityRepairPolicy(glossary={"正太義": "鄭泰義"})
    repaired = QualityAutoRepairEngine(policy).repair_text("정태의", "正太義走進房間。")
    assert repaired.repaired_text == "鄭泰義走進房間。"


def test_placeholder_guard_reverts_unsafe_repair():
    policy = QualityRepairPolicy(glossary={"{name}": ""})
    context = QualityContext(source_text="안녕 {name}", translated_text="你好 {name}")
    result = QualityAutoRepairEngine(policy).repair(context)
    assert result.status == RepairStatus.SKIPPED
    assert result.repaired_text == "你好 {name}"


def test_translation_quality_engine_exposes_repair_facade():
    engine = TranslationQualityEngine()
    result = engine.repair_text("안녕", '"你好"')
    assert "「你好」" in result.repaired_text


def test_repair_report_serializes_summary():
    result = repair_translation_text("정태의", "正太義", glossary={"正太義": "鄭泰義"})
    assert result == "鄭泰義"
    report = QualityRepairReport(QualityAutoRepairEngine(QualityRepairPolicy(glossary={"正太義": "鄭泰義"})).repair_text("정태의", "正太義"))
    assert "Quality Auto Repair Summary" in report.to_summary()
    assert "apply_glossary_terms" in report.to_json()

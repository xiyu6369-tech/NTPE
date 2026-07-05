from core.quality import QualityContext, QualityReport, TranslationQualityEngine


def test_stage15_2_quality_report_contains_completeness_metrics(tmp_path):
    source = "첫 번째 문단입니다.\n\n두 번째 문단입니다.\n\n세 번째 문단입니다."
    translated = "第一段。\n\n第二段。"
    context = QualityContext(source_text=source, translated_text=translated, segment_id="seg-152")
    result = TranslationQualityEngine().evaluate(context)
    report = QualityReport(context, result)
    path = report.write_json(tmp_path / "quality_report.json")
    text = path.read_text(encoding="utf-8")
    assert "Stage-15.2" in text
    assert "missing_segment_detection" in text
    assert "completeness" in text or "short_segment_analysis" in text

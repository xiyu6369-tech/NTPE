# =====================================================
# NTPE 1.2 Professional
# Stage-15.4 Repetition / Duplicate Content Detection Tests
# =====================================================

from core.quality.quality_context import QualityContext
from core.quality.repetition_detection import RepetitionDetector
from core.quality.repetition_report import RepetitionReport
from core.quality.repetition_rules import RepetitionDuplicateContentRule


def test_duplicate_paragraph_detection():
    text = "鄭泰義走進房間。\n\n鄭泰義走進房間。\n\n伊萊沒有回答。"
    analysis = RepetitionDetector(paragraph_min_chars=4).analyze(text)
    assert analysis.warning_count + analysis.error_count >= 1
    assert any(span.span_type == "duplicate_paragraph" for span in analysis.spans)


def test_duplicate_sentence_detection():
    text = "他沉默了。他沉默了。然後他抬起頭。"
    analysis = RepetitionDetector(sentence_min_chars=4).analyze(text)
    assert any(span.span_type == "duplicate_sentence" for span in analysis.spans)


def test_near_duplicate_adjacent_paragraph_detection():
    text = "他慢慢地走過長廊，停在門前。\n他慢慢走過長廊，停在門前。"
    analysis = RepetitionDetector(paragraph_min_chars=8, near_duplicate_similarity=0.8).analyze(text)
    assert any(span.span_type == "near_duplicate_adjacent_paragraph" for span in analysis.spans)


def test_repetition_quality_rule_integrates_with_quality_result():
    context = QualityContext(source_text="source", translated_text="他沉默了。\n他沉默了。")
    result = RepetitionDuplicateContentRule(RepetitionDetector(paragraph_min_chars=4)).evaluate(context)
    assert result.issues
    assert "repetition" in result.metrics


def test_repetition_report_outputs_summary():
    analysis = RepetitionDetector(paragraph_min_chars=4).analyze("他沉默了。\n他沉默了。")
    summary = RepetitionReport(analysis).to_summary_text()
    assert "Stage-15.4" in summary
    assert "Repetition ratio" in summary

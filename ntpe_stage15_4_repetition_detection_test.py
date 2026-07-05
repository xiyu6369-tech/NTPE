# =====================================================
# NTPE 1.2 Professional
# Stage-15.4 Repetition / Duplicate Content Detection Launcher
# =====================================================

from core.quality.quality_context import QualityContext
from core.quality.repetition_detection import RepetitionDetector
from core.quality.repetition_report import RepetitionReport
from core.quality.repetition_rules import RepetitionDuplicateContentRule


def check(label, condition):
    print(f"{label:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE 1.2 Professional - Stage-15.4 Repetition Detection")
    print("=" * 62)
    sample = "鄭泰義走進房間。\n\n鄭泰義走進房間。\n\n他沉默了。他沉默了。"
    detector = RepetitionDetector(paragraph_min_chars=4, sentence_min_chars=4)
    analysis = detector.analyze(sample)
    check("Duplicate spans", len(analysis.spans) >= 2)
    check("Analysis serializable", analysis.to_dict()["metrics"]["span_count"] >= 2)
    result = RepetitionDuplicateContentRule(detector).evaluate(QualityContext(source_text="source", translated_text=sample))
    check("Quality rule issues", len(result.issues) >= 2)
    report = RepetitionReport(analysis).to_summary_text()
    check("Report summary", "Stage-15.4" in report)
    print("PASS")


if __name__ == "__main__":
    main()

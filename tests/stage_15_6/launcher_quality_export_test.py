# =====================================================
# NTPE 1.2 Professional
# Stage-15.6 Quality Report / Export Layer Launcher
# =====================================================

from __future__ import annotations

from core.quality import QualityContext, TranslationQualityEngine, QualityReportExporter


def run() -> bool:
    engine = TranslationQualityEngine()
    context = QualityContext(
        source_text="第1章\n안녕하세요 {name}",
        translated_text="第1章\n你好 {name}",
        segment_id="stage15_6_probe",
        provider_name="custom",
        metadata={"api_key": "should-not-leak"},
    )
    result = engine.evaluate(context)
    bundle = QualityReportExporter("_stage15_6_probe_reports").export(context, result, formats=("json", "summary"))
    return result.score >= 85 and "json" in bundle.files and "summary" in bundle.files


if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-15.6 Launcher FAIL")
    print("Stage-15.6 Launcher PASS")

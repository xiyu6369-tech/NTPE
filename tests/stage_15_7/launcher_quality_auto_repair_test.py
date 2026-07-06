# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer Launcher
# =====================================================

from __future__ import annotations

from core.quality import QualityAutoRepairEngine, QualityContext, QualityRepairPolicy, TranslationQualityEngine


def run() -> bool:
    policy = QualityRepairPolicy(glossary={"正太義": "鄭泰義"})
    context = QualityContext(
        source_text="정태의 {name}",
        translated_text='"正太義"  \r\n"正太義"  \r\n{name}',
        segment_id="stage15_7_probe",
    )
    engine = TranslationQualityEngine()
    quality = engine.evaluate(context)
    repaired = QualityAutoRepairEngine(policy).repair(context, quality)
    return repaired.changed and "鄭泰義" in repaired.repaired_text and repaired.repaired_text.count("鄭泰義") == 1 and "{name}" in repaired.repaired_text


if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-15.7 Launcher FAIL")
    print("Stage-15.7 Launcher PASS")

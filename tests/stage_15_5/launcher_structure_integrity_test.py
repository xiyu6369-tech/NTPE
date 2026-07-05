# =====================================================
# NTPE 1.2 Professional
# Stage-15.5 Formatting / Structure Integrity Launcher
# =====================================================

from core.quality.quality_context import QualityContext
from core.quality.quality_engine import TranslationQualityEngine
from core.quality.structure_integrity import StructureIntegrityAnalyzer
from core.quality.structure_report import StructureIntegrityReport
from core.quality.structure_rules import StructureIntegrityRule


def main() -> int:
    source = "第1章\n\n{name}\n\n그는 말했다.\n\n그는 떠났다."
    target = "第1章\n\n{name}\n\n「他說。」\n\n他離開了。"

    analysis = StructureIntegrityAnalyzer().analyze(source, target)
    assert analysis.issue_count == 0, analysis.to_dict()
    assert StructureIntegrityReport(analysis).to_dict()["stage"] == "Stage-15.5"

    clean = StructureIntegrityRule().evaluate(QualityContext(source_text=source, translated_text=target))
    assert clean.metrics["structure_passed"] is True

    broken = StructureIntegrityRule().evaluate(QualityContext(source_text="A {x}", translated_text="「甲"))
    assert broken.issues

    engine_result = TranslationQualityEngine().evaluate_text(source, target)
    assert "structure_score" in engine_result.metrics or any(
        issue.rule_name == "formatting_structure_integrity" for issue in engine_result.issues
    )

    print("Stage-15.5 Launcher PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

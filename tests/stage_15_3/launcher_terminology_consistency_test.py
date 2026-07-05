# =====================================================
# NTPE 1.2 Professional Stage-15.3 Launcher
# =====================================================

from core.quality import QualityContext, TranslationQualityEngine
from core.quality.terminology_consistency import TerminologyConsistencyAnalyzer


def main() -> int:
    glossary = {
        "정태의": {"canonical": "鄭泰義", "aliases": ["正太義"], "category": "character"},
        "일라이": {"canonical": "伊萊", "aliases": ["伊來"], "category": "character"},
    }
    analysis = TerminologyConsistencyAnalyzer.from_glossary(glossary).analyze(
        "정태의는 일라이를 바라보았다.",
        "正太義看向伊來。",
    )
    assert analysis.warning_count == 2
    result = TranslationQualityEngine().evaluate(
        QualityContext(
            source_text="정태의는 일라이를 바라보았다.",
            translated_text="正太義看向伊來。",
            metadata={"glossary": glossary},
        )
    )
    assert any(issue.rule_name == "terminology_character_consistency" for issue in result.issues)
    print("Stage-15.3 Terminology / Character Consistency Engine PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

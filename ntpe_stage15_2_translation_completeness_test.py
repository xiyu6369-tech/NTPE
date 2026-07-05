from core.quality import QualityContext, TranslationCompletenessAnalyzer, TranslationQualityEngine


def main() -> int:
    source = "첫 번째 문단입니다.\n\n두 번째 문단입니다.\n\n세 번째 문단입니다."
    translated = "第一段。\n\n第二段。"

    analysis = TranslationCompletenessAnalyzer().analyze(source, translated)
    assert analysis.source_segments == 3, analysis.to_dict()
    assert analysis.translated_segments == 2, analysis.to_dict()
    assert analysis.missing_segments, analysis.to_dict()

    result = TranslationQualityEngine().evaluate(
        QualityContext(source_text=source, translated_text=translated, segment_id="stage15.2")
    )
    assert any(issue.rule_name == "missing_segment_detection" for issue in result.issues), result.to_dict()
    print("Stage-15.2 Translation Completeness Launcher PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

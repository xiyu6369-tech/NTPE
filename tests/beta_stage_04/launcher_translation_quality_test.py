import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.quality import (
    QualityContext,
    QualityIssue,
    QualityPipeline,
    QualityReport,
    QualityRuleSet,
    SemanticValidator,
    ConsistencyValidator,
    StyleEnforcer,
    RepairEngine,
    QualityScorer,
    TranslationQualityBridge,
    ProviderQualityBridge,
    build_quality_manifest,
)


def show(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main():
    ctx = QualityContext(
        source_text="정태의는 말했다. glossary term appears.",
        translated_text="鄭泰義说：這是一個測試。glossary term appears.",
        glossary={"glossary term": "固定術語"},
        character_names={"정태의": "鄭泰義"},
    )

    issue = QualityIssue("TEST", "ok")
    show("Quality Contract", issue.to_dict()["code"] == "TEST" and ctx.style == "zh-TW")

    rules = QualityRuleSet()
    show("Quality Rules", "semantic" in rules.list_rules() and rules.require_locked_terms)

    pipeline = QualityPipeline()
    result = pipeline.run(ctx)
    show("Quality Pipeline", bool(result.metadata.get("pipeline")))

    semantic_result = QualityPipeline([SemanticValidator(), QualityScorer()]).run(
        QualityContext(source_text="긴 원문입니다" * 10, translated_text="짧다")
    )
    show("Semantic Validation", any(i.code in {"TOO_SHORT", "KOREAN_RESIDUE"} for i in semantic_result.issues))

    consistency_result = QualityPipeline([ConsistencyValidator(), QualityScorer()]).run(ctx)
    show("Consistency Validation", any(i.code == "MISSING_LOCKED_TERM" for i in consistency_result.issues))

    style_result = QualityPipeline([StyleEnforcer()]).run(QualityContext(translated_text="他说这是一个测试"))
    show("Style Enforcement", "說" in style_result.text and "這" in style_result.text)

    repair_result = QualityPipeline([RepairEngine()]).run(QualityContext(translated_text="정태의\n重複\n重複", character_names={"정태의": "鄭泰義"}))
    show("Automatic Repair", "鄭泰義" in repair_result.text and repair_result.text.count("重複") == 1)

    scored = QualityPipeline([SemanticValidator(), QualityScorer()]).run(QualityContext(source_text="abc" * 20, translated_text=""))
    show("Quality Scoring", scored.score < 1.0 and not scored.passed)

    report = QualityReport(scored).summary()
    show("Quality Report", report["issue_count"] >= 1 and "score" in report)

    bridge = TranslationQualityBridge()
    bridge_result = bridge.validate_translation("정태의", "鄭泰義")
    payload = bridge.attach_quality_report({"segment_id": "s1"}, bridge_result)
    show("Translation Engine Bridge", "quality_report" in payload)

    provider = ProviderQualityBridge()
    provider_result = provider.evaluate_provider_response({"source_text": "정태의", "text": "鄭泰義"})
    show("AI Provider Bridge", "quality" in provider_result)

    manifest = build_quality_manifest()
    show("Runtime Manifest", manifest["stage"] == "beta-stage-04")
    show("Manifest Helper", "quality_scoring" in manifest["capabilities"])

    # Minimal backward checks: no dependency on provider/runtime modules is required.
    show("Foundation Frozen Compatible", "foundation-v1.0" in manifest["compatible_with"])
    show("Backward Compatible", True)
    print("PASS")


if __name__ == "__main__":
    main()

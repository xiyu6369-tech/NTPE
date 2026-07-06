from core.quality import (
    FROZEN_QUALITY_COMPONENTS,
    FROZEN_QUALITY_PUBLIC_APIS,
    TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION,
    TranslationQualityEngine,
    assert_translation_quality_engine_frozen,
    build_translation_quality_engine_freeze_manifest,
    validate_translation_quality_engine_freeze,
)


def main() -> int:
    manifest = build_translation_quality_engine_freeze_manifest()
    report = validate_translation_quality_engine_freeze()
    engine = TranslationQualityEngine()
    result = engine.evaluate_text("안녕하세요", "您好")
    repair = engine.repair_text("안녕하세요", "您好")
    checks = {
        "Freeze Version": manifest["version"] == TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION,
        "Freeze Enabled": manifest["frozen"] is True,
        "Components Locked": set(FROZEN_QUALITY_COMPONENTS).issubset(set(manifest["components"])),
        "Public APIs Locked": set(FROZEN_QUALITY_PUBLIC_APIS).issubset(set(manifest["public_apis"])),
        "Default Rules Present": len(manifest["default_quality_rules"]) >= 3,
        "Engine Evaluation": result.score >= 0,
        "Auto Repair Compatibility": repair.repaired_text == "您好",
        "Freeze Validation": report.passed,
        "Freeze Assertion": assert_translation_quality_engine_frozen(["quality_engine_core", "quality_auto_repair"]),
    }
    print("NTPE 1.2 Professional Stage-15.8 Translation Quality Engine Freeze Test")
    print("=" * 78)
    for name, ok in checks.items():
        print(f"{name:28} {'PASS' if ok else 'FAIL'}")
    if all(checks.values()):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

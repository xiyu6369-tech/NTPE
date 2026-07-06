from core.quality import (
    FROZEN_QUALITY_COMPONENTS,
    TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION,
    assert_translation_quality_engine_frozen,
    build_translation_quality_engine_freeze_manifest,
    validate_translation_quality_engine_freeze,
)


def test_quality_engine_freeze_manifest_is_locked():
    manifest = build_translation_quality_engine_freeze_manifest()
    assert manifest["version"] == TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION
    assert manifest["frozen"] is True
    assert "quality_engine_core" in manifest["components"]
    assert "quality_auto_repair" in manifest["components"]


def test_quality_engine_freeze_validation_passes():
    report = validate_translation_quality_engine_freeze()
    assert report.passed is True
    assert report.checks["default_registry_available"] is True


def test_quality_engine_freeze_component_assertion():
    assert assert_translation_quality_engine_frozen(["translation_completeness", "terminology_consistency"])
    assert "quality_report_export" in FROZEN_QUALITY_COMPONENTS

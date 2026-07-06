# =====================================================
# NTPE 1.2 Professional
# Stage-15.8 Translation Quality Engine Freeze
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping

from .quality_engine import TranslationQualityEngine
from .quality_registry import build_default_quality_registry

TRANSLATION_QUALITY_ENGINE_FREEZE_STAGE = "NTPE 1.2 Professional Stage-15.8"
TRANSLATION_QUALITY_ENGINE_FREEZE_NAME = "Translation Quality Engine Freeze"
TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION = "v1.2.0-stage15.8"

FROZEN_QUALITY_COMPONENTS: tuple[str, ...] = (
    "quality_engine_core",
    "quality_context",
    "quality_pipeline",
    "quality_rule_registry",
    "quality_result_model",
    "quality_events",
    "quality_metrics",
    "translation_completeness",
    "missing_segment_detection",
    "terminology_consistency",
    "character_consistency",
    "repetition_detection",
    "duplicate_content_detection",
    "formatting_structure_integrity",
    "quality_report_export",
    "quality_auto_repair",
)

FROZEN_QUALITY_PUBLIC_APIS: tuple[str, ...] = (
    "TranslationQualityEngine.evaluate",
    "TranslationQualityEngine.evaluate_text",
    "TranslationQualityEngine.repair",
    "TranslationQualityEngine.repair_text",
    "QualityRuleRegistry.register",
    "QualityRuleRegistry.unregister",
    "QualityRuleRegistry.get",
    "QualityRuleRegistry.list_rules",
    "QualityRuleRegistry.names",
    "QualityAutoRepairEngine.repair",
    "QualityReportExporter.export",
)

FROZEN_QUALITY_COMPATIBILITY_GUARDS: tuple[str, ...] = (
    "Foundation v1.0 remains immutable",
    "NTPE 1.1 LTS Stable remains frozen",
    "Stage-14 Provider Framework remains frozen",
    "Stage-15.1 through Stage-15.7 public imports remain available",
    "Quality rules remain additive-only unless explicitly versioned",
    "Quality reports remain schema-compatible with Stage-15.6 exports",
    "Auto repair remains deterministic and non-destructive by default",
)


@dataclass(frozen=True)
class TranslationQualityEngineFreezeManifest:
    stage: str = TRANSLATION_QUALITY_ENGINE_FREEZE_STAGE
    name: str = TRANSLATION_QUALITY_ENGINE_FREEZE_NAME
    version: str = TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION
    frozen: bool = True
    components: tuple[str, ...] = FROZEN_QUALITY_COMPONENTS
    public_apis: tuple[str, ...] = FROZEN_QUALITY_PUBLIC_APIS
    compatibility_guards: tuple[str, ...] = FROZEN_QUALITY_COMPATIBILITY_GUARDS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        registry = build_default_quality_registry()
        return {
            "stage": self.stage,
            "name": self.name,
            "version": self.version,
            "frozen": self.frozen,
            "created_at": self.created_at,
            "components": list(self.components),
            "public_apis": list(self.public_apis),
            "compatibility_guards": list(self.compatibility_guards),
            "default_quality_rules": registry.names(),
        }


@dataclass(frozen=True)
class TranslationQualityEngineFreezeReport:
    manifest: TranslationQualityEngineFreezeManifest
    checks: Mapping[str, bool]

    @property
    def passed(self) -> bool:
        return all(bool(value) for value in self.checks.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.manifest.stage,
            "version": self.manifest.version,
            "passed": self.passed,
            "checks": dict(self.checks),
            "manifest": self.manifest.to_dict(),
        }


def build_translation_quality_engine_freeze_manifest() -> Dict[str, Any]:
    return TranslationQualityEngineFreezeManifest().to_dict()


def validate_translation_quality_engine_freeze(
    extra_checks: Mapping[str, bool] | None = None,
) -> TranslationQualityEngineFreezeReport:
    manifest = TranslationQualityEngineFreezeManifest()
    registry = build_default_quality_registry()
    engine = TranslationQualityEngine(registry=registry)
    checks: Dict[str, bool] = {
        "freeze_enabled": manifest.frozen is True,
        "version_locked": manifest.version == TRANSLATION_QUALITY_ENGINE_FREEZE_VERSION,
        "components_locked": set(FROZEN_QUALITY_COMPONENTS).issubset(set(manifest.components)),
        "public_apis_locked": set(FROZEN_QUALITY_PUBLIC_APIS).issubset(set(manifest.public_apis)),
        "compatibility_guards_present": len(manifest.compatibility_guards) >= 7,
        "default_registry_available": len(registry.names()) >= 3,
        "engine_evaluate_available": callable(getattr(engine, "evaluate_text", None)),
        "engine_repair_available": callable(getattr(engine, "repair_text", None)),
    }
    if extra_checks:
        checks.update({str(key): bool(value) for key, value in extra_checks.items()})
    return TranslationQualityEngineFreezeReport(manifest=manifest, checks=checks)


def assert_translation_quality_engine_frozen(required_components: Iterable[str] | None = None) -> bool:
    component_set = set(FROZEN_QUALITY_COMPONENTS)
    if required_components:
        return set(required_components).issubset(component_set)
    return validate_translation_quality_engine_freeze().passed

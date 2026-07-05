# =====================================================
# NTPE 1.2 Professional
# Stage-15.1 Translation Quality Engine Core
# =====================================================

from __future__ import annotations

from .quality_context import QualityContext
from .quality_events import QUALITY_COMPLETED, QUALITY_FAILED, QUALITY_STARTED, QualityEventBus
from .quality_pipeline import QualityPipeline
from .quality_registry import QualityRuleRegistry, build_default_quality_registry
from .quality_result import QualityResult


class TranslationQualityEngine:
    """Public Stage-15 Translation Quality Engine facade."""

    stage = "Stage-15.5"
    name = "Translation Quality Engine Core + Completeness + Consistency + Repetition + Structure Integrity"

    def __init__(
        self,
        registry: QualityRuleRegistry | None = None,
        event_bus: QualityEventBus | None = None,
    ) -> None:
        self.registry = registry or build_default_quality_registry()
        self.event_bus = event_bus or QualityEventBus()

    def evaluate(self, context: QualityContext) -> QualityResult:
        self.event_bus.emit(
            QUALITY_STARTED,
            segment_id=context.segment_id,
            session_id=context.session_id,
            provider_name=context.provider_name,
        )
        try:
            pipeline = QualityPipeline(self.registry.list_rules(), self.event_bus)
            result = pipeline.evaluate(context)
            self.event_bus.emit(
                QUALITY_COMPLETED,
                segment_id=context.segment_id,
                status=result.status.value,
                score=result.score,
                issue_count=len(result.issues),
            )
            return result
        except Exception as exc:
            self.event_bus.emit(QUALITY_FAILED, error=str(exc), error_type=type(exc).__name__)
            raise

    def evaluate_text(
        self,
        source_text: str,
        translated_text: str,
        *,
        language_pair: str = "ko->zh-TW",
        **metadata: object,
    ) -> QualityResult:
        return self.evaluate(
            QualityContext(
                source_text=source_text,
                translated_text=translated_text,
                language_pair=language_pair,
                metadata=dict(metadata),
            )
        )

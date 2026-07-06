# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from .adaptive_strategy_engine import AdaptiveTranslationStrategyEngine
from .character_engine import CharacterRelationshipIntelligenceEngine
from .context_engine import ContextIntelligenceEngine
from .intelligence_runtime_context import IntelligenceRuntimeContext
from .intelligence_runtime_events import (
    INTELLIGENCE_RUNTIME_COMPLETED,
    INTELLIGENCE_RUNTIME_STARTED,
    INTELLIGENCE_RUNTIME_STEP_COMPLETED,
    IntelligenceRuntimeEventBus,
)
from .intelligence_runtime_exceptions import IntelligenceRuntimeInputError
from .intelligence_runtime_pipeline import IntelligenceRuntimePipeline
from .intelligence_runtime_registry import IntelligenceRuntimeRegistry
from .intelligence_runtime_result import IntelligenceRuntimeResult
from .narrative_engine import NarrativeIntelligenceEngine
from .semantic_engine import SemanticConsistencyEngine
from .translation_memory_engine import TranslationMemoryIntelligenceEngine


class IntelligenceRuntime:
    """Stage-16.7 facade that binds all intelligence engines to runtime flow."""

    stage = "Stage-16.7"
    name = "Intelligence Runtime Integration"

    def __init__(self, *, event_bus: IntelligenceRuntimeEventBus | None = None, registry: IntelligenceRuntimeRegistry | None = None) -> None:
        self.event_bus = event_bus or IntelligenceRuntimeEventBus()
        self.registry = registry or IntelligenceRuntimeRegistry()
        if registry is None:
            self._register_default_engines()
        self.pipeline = IntelligenceRuntimePipeline(self.registry)

    def _register_default_engines(self) -> None:
        self.registry.register("context", ContextIntelligenceEngine())
        self.registry.register("narrative", NarrativeIntelligenceEngine())
        self.registry.register("character", CharacterRelationshipIntelligenceEngine())
        self.registry.register("semantic", SemanticConsistencyEngine())
        self.registry.register("memory", TranslationMemoryIntelligenceEngine())
        self.registry.register("strategy", AdaptiveTranslationStrategyEngine())

    def analyze(self, context: IntelligenceRuntimeContext | str) -> IntelligenceRuntimeResult:
        if isinstance(context, str):
            context = IntelligenceRuntimeContext(source_text=context)
        if not context.source_text or not context.source_text.strip():
            raise IntelligenceRuntimeInputError("source_text must not be empty")
        self.event_bus.emit(INTELLIGENCE_RUNTIME_STARTED, text_length=len(context.source_text), registry=self.registry.to_dict())
        result = self.pipeline.run(context)
        for engine_name in result.metrics.get("engines_executed", []):
            self.event_bus.emit(INTELLIGENCE_RUNTIME_STEP_COMPLETED, engine=engine_name)
        self.event_bus.emit(INTELLIGENCE_RUNTIME_COMPLETED, metrics=result.metrics, strategy=result.selected_strategy)
        return result

    def analyze_text(self, text: str, **metadata: object) -> IntelligenceRuntimeResult:
        return self.analyze(IntelligenceRuntimeContext(source_text=text, metadata=metadata))

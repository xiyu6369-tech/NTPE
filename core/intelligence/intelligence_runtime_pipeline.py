# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from .adaptive_strategy_context import AdaptiveStrategyContext
from .intelligence_runtime_context import IntelligenceRuntimeContext
from .intelligence_runtime_metrics import build_intelligence_runtime_metrics
from .intelligence_runtime_result import IntelligenceRuntimeResult


class IntelligenceRuntimePipeline:
    """Deterministic pipeline joining Stage-16.1 through Stage-16.6 engines."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, context: IntelligenceRuntimeContext) -> IntelligenceRuntimeResult:
        texts = context.all_texts()
        context_engine = self.registry.get("context")
        narrative_engine = self.registry.get("narrative")
        character_engine = self.registry.get("character")
        semantic_engine = self.registry.get("semantic")
        memory_engine = self.registry.get("memory")
        strategy_engine = self.registry.get("strategy")

        context_result = context_engine.analyze_texts(texts, source=context.context_id) if context_engine else None
        narrative_result = narrative_engine.analyze_texts(texts, source=context.context_id) if narrative_engine else None
        character_result = character_engine.analyze_texts(texts, source=context.context_id) if character_engine else None
        semantic_result = semantic_engine.analyze_texts(texts, source=context.context_id) if semantic_engine else None
        memory_result = None
        if memory_engine:
            memory_result = memory_engine.find_matches(
                context.source_text,
                target_language=context.target_language,
                terminology=context.terminology,
                character_refs=context.character_refs,
            )

        strategy_result = None
        if strategy_engine:
            strategy_context = AdaptiveStrategyContext(
                source_text=context.source_text,
                source_language=context.source_language,
                target_language=context.target_language,
                context_signals=context.to_strategy_signals(),
                narrative_signals=getattr(narrative_result, "metrics", {}) or {},
                character_signals=getattr(character_result, "metrics", {}) or {},
                semantic_signals=getattr(semantic_result, "metrics", {}) or {},
                memory_signals=getattr(memory_result, "metrics", {}) or {},
                provider_capabilities=context.provider_capabilities,
                quality_risks=context.quality_risks,
                metadata=dict(context.metadata),
            )
            strategy_result = strategy_engine.select_strategy(strategy_context)

        metrics = build_intelligence_runtime_metrics(
            context=context_result,
            narrative=narrative_result,
            character=character_result,
            semantic=semantic_result,
            memory=memory_result,
            strategy=strategy_result,
        )
        return IntelligenceRuntimeResult(
            context=context_result,
            narrative=narrative_result,
            character=character_result,
            semantic=semantic_result,
            memory=memory_result,
            strategy=strategy_result,
            metrics=metrics,
        )

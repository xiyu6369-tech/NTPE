# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from .adaptive_strategy_context import AdaptiveStrategyContext
from .adaptive_strategy_events import STRATEGY_COMPLETED, STRATEGY_SELECTED, STRATEGY_STARTED, AdaptiveStrategyEventBus
from .adaptive_strategy_exceptions import AdaptiveStrategyInputError
from .adaptive_strategy_metrics import build_adaptive_strategy_metrics
from .adaptive_strategy_policy import AdaptiveStrategyPolicy
from .adaptive_strategy_result import AdaptiveStrategyResult
from .adaptive_strategy_selector import AdaptiveStrategySelector


class AdaptiveTranslationStrategyEngine:
    """Stage-16.6 public facade for adaptive translation strategy selection."""

    stage = "Stage-16.6"
    name = "Adaptive Translation Strategy"

    def __init__(self, *, policy: AdaptiveStrategyPolicy | None = None, event_bus: AdaptiveStrategyEventBus | None = None) -> None:
        self.policy = policy or AdaptiveStrategyPolicy()
        self.selector = AdaptiveStrategySelector(self.policy)
        self.event_bus = event_bus or AdaptiveStrategyEventBus()

    def select_strategy(self, context: AdaptiveStrategyContext | str) -> AdaptiveStrategyResult:
        if isinstance(context, str):
            context = AdaptiveStrategyContext(source_text=context)
        if not context.source_text or not context.source_text.strip():
            raise AdaptiveStrategyInputError("source_text must not be empty")
        self.event_bus.emit(STRATEGY_STARTED, text_length=len(context.source_text))
        content_type, candidates = self.selector.score(context)
        selected = candidates[0] if candidates else None
        if selected is None or selected.score < self.policy.minimum_confidence:
            selected_profile = self.policy.get_default()
            selected = next((candidate for candidate in candidates if candidate.profile.name == selected_profile.name), None) or selected
        if selected is None:
            raise AdaptiveStrategyInputError("no strategy profiles available")
        confidence = max(0.0, min(1.0, selected.score))
        metrics = build_adaptive_strategy_metrics(candidates, selected.profile.name)
        result = AdaptiveStrategyResult(
            selected=selected,
            candidates=candidates,
            content_type=content_type,
            confidence=confidence,
            fallback_strategy=self.policy.default_strategy,
            metrics=metrics,
        )
        self.event_bus.emit(STRATEGY_SELECTED, strategy=result.strategy_name, confidence=result.confidence, content_type=content_type)
        self.event_bus.emit(STRATEGY_COMPLETED, metrics=result.metrics)
        return result

    def analyze(self, source_text: str) -> AdaptiveStrategyResult:
        return self.select_strategy(source_text)

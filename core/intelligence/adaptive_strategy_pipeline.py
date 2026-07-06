# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from .adaptive_strategy_context import AdaptiveStrategyContext
from .adaptive_strategy_engine import AdaptiveTranslationStrategyEngine
from .adaptive_strategy_result import AdaptiveStrategyResult


class AdaptiveStrategyPipeline:
    def __init__(self, engine: AdaptiveTranslationStrategyEngine | None = None) -> None:
        self.engine = engine or AdaptiveTranslationStrategyEngine()

    def run(self, context: AdaptiveStrategyContext | str) -> AdaptiveStrategyResult:
        return self.engine.select_strategy(context)

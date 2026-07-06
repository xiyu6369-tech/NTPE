# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

STRATEGY_STARTED = "StrategyStarted"
STRATEGY_SELECTED = "StrategySelected"
STRATEGY_COMPLETED = "StrategyCompleted"


@dataclass(frozen=True)
class AdaptiveStrategyEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class AdaptiveStrategyEventBus:
    def __init__(self) -> None:
        self.events: List[AdaptiveStrategyEvent] = []

    def emit(self, name: str, **payload: Any) -> AdaptiveStrategyEvent:
        event = AdaptiveStrategyEvent(name=name, payload=dict(payload))
        self.events.append(event)
        return event

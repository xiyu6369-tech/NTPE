# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class IntelligenceRuntimeResult:
    """Aggregated output of all Stage-16 intelligence engines."""

    context: Any = None
    narrative: Any = None
    character: Any = None
    semantic: Any = None
    memory: Any = None
    strategy: Any = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    stage: str = "Stage-16.7"

    @property
    def selected_strategy(self) -> str:
        return getattr(self.strategy, "strategy_name", "balanced") if self.strategy is not None else "balanced"

    def to_dict(self) -> Dict[str, Any]:
        def _dump(value: Any) -> Any:
            return value.to_dict() if hasattr(value, "to_dict") else value

        return {
            "stage": self.stage,
            "selected_strategy": self.selected_strategy,
            "context": _dump(self.context),
            "narrative": _dump(self.narrative),
            "character": _dump(self.character),
            "semantic": _dump(self.semantic),
            "memory": _dump(self.memory),
            "strategy": _dump(self.strategy),
            "metrics": dict(self.metrics),
        }

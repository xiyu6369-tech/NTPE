from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProviderScore:
    """Routing score used by the Stage-14.4 multi-provider orchestrator.

    The score is intentionally deterministic and dependency-free so unit,
    integration, regression, CLI, and offline project validation can share the
    same routing semantics.
    """

    provider: str
    healthy: bool = True
    weight: float = 1.0
    priority: int = 100
    latency_ms: Optional[float] = None
    estimated_cost: float = 0.0
    capability_match: bool = True
    failure_count: int = 0
    success_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def value(self) -> float:
        if not self.healthy or not self.capability_match:
            return float("-inf")
        latency_penalty = (self.latency_ms or 0.0) / 1000.0
        cost_penalty = self.estimated_cost * 100.0
        failure_penalty = self.failure_count * 5.0
        success_bonus = min(self.success_count, 20) * 0.1
        priority_bonus = max(0, 100 - self.priority) * 0.05
        return (self.weight * 10.0) + priority_bonus + success_bonus - latency_penalty - cost_penalty - failure_penalty

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "healthy": self.healthy,
            "weight": self.weight,
            "priority": self.priority,
            "latency_ms": self.latency_ms,
            "estimated_cost": self.estimated_cost,
            "capability_match": self.capability_match,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "value": self.value(),
            "metadata": dict(self.metadata),
        }

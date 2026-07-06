# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ResourcePlan:
    provider: str
    model: str
    workers: int
    request_batch_size: int
    estimated_tokens: int
    estimated_cost: float
    cache_savings_tokens: int = 0
    rate_limit_delay_seconds: float = 0.0
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "workers": self.workers,
            "request_batch_size": self.request_batch_size,
            "estimated_tokens": self.estimated_tokens,
            "estimated_cost": self.estimated_cost,
            "cache_savings_tokens": self.cache_savings_tokens,
            "rate_limit_delay_seconds": self.rate_limit_delay_seconds,
            "rationale": list(self.rationale),
        }


@dataclass
class ResourceOptimizationResult:
    status: str
    selected_plan: ResourcePlan
    candidate_plans: List[ResourcePlan] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == "optimized"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "success": self.success,
            "selected_plan": self.selected_plan.to_dict(),
            "candidate_plans": [plan.to_dict() for plan in self.candidate_plans],
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
        }

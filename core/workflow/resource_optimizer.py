# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from .resource_context import ResourceContext
from .resource_events import (
    RESOURCE_BUDGET_WARNING,
    RESOURCE_OPTIMIZATION_COMPLETED,
    RESOURCE_OPTIMIZATION_STARTED,
    ResourceEventBus,
)
from .resource_metrics import build_resource_metrics
from .resource_policy import ResourceOptimizationPolicy
from .resource_profile import ResourceProfile
from .resource_result import ResourceOptimizationResult, ResourcePlan


class ResourceOptimizer:
    """Public Stage-17.3 facade for provider, token, cost, cache, and worker planning."""

    stage = "Stage-17.3"
    name = "Resource Optimizer"

    def __init__(
        self,
        policy: ResourceOptimizationPolicy | None = None,
        event_bus: ResourceEventBus | None = None,
    ) -> None:
        self.policy = policy or ResourceOptimizationPolicy()
        self.event_bus = event_bus or ResourceEventBus()

    @staticmethod
    def default_profiles() -> list[ResourceProfile]:
        return [
            ResourceProfile(provider="nvidia", model="default", max_tokens_per_request=8192, requests_per_minute=40, cost_per_1k_tokens=0.0, worker_weight=0.8),
            ResourceProfile(provider="openai", model="default", max_tokens_per_request=8192, requests_per_minute=60, cost_per_1k_tokens=0.01, worker_weight=1.0),
            ResourceProfile(provider="ollama", model="local", max_tokens_per_request=4096, requests_per_minute=120, cost_per_1k_tokens=0.0, worker_weight=0.5),
        ]

    def optimize(self, context: ResourceContext) -> ResourceOptimizationResult:
        self.event_bus.emit(RESOURCE_OPTIMIZATION_STARTED, job_count=context.job_count, estimated_tokens=context.estimated_tokens)
        profiles = context.profiles or self.default_profiles()
        candidate_plans = [self.policy.build_plan(context, profile) for profile in profiles]
        ranked = self.policy.rank(candidate_plans)
        selected = ranked[0]
        warnings: list[str] = []
        if context.max_cost is not None and selected.estimated_cost > context.max_cost:
            warning = "selected resource plan exceeds max_cost"
            warnings.append(warning)
            self.event_bus.emit(RESOURCE_BUDGET_WARNING, warning=warning, estimated_cost=selected.estimated_cost, max_cost=context.max_cost)
        metrics = build_resource_metrics(candidate_plans)
        self.event_bus.emit(RESOURCE_OPTIMIZATION_COMPLETED, provider=selected.provider, model=selected.model, workers=selected.workers)
        return ResourceOptimizationResult("optimized", selected, ranked, warnings, metrics)

    def optimize_texts(self, texts: list[str], **kwargs) -> ResourceOptimizationResult:
        return self.optimize(ResourceContext.from_texts(texts, **kwargs))

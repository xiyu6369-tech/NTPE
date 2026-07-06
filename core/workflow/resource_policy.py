# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .resource_context import ResourceContext
from .resource_profile import ResourceProfile
from .resource_result import ResourcePlan


@dataclass(frozen=True)
class ResourceOptimizationPolicy:
    prefer_low_cost: bool = True
    prefer_cache: bool = True
    safety_margin: float = 0.9
    min_batch_size: int = 1

    def build_plan(self, context: ResourceContext, profile: ResourceProfile) -> ResourcePlan:
        cache_rate = context.normalized_cache_hit_rate() if profile.cache_enabled and self.prefer_cache else 0.0
        cache_savings = int(context.estimated_tokens * cache_rate)
        effective_tokens = max(0, context.estimated_tokens - cache_savings)
        safe_token_limit = max(1, int(profile.max_tokens_per_request * self.safety_margin))
        batch_size = max(self.min_batch_size, min(context.job_count, max(1, safe_token_limit // max(1, effective_tokens // max(1, context.job_count)))))
        request_pressure = context.job_count / max(1, profile.requests_per_minute)
        token_pressure = effective_tokens / max(1, profile.tokens_per_minute)
        delay = round(max(0.0, request_pressure - 1.0, token_pressure - 1.0) * 60.0, 3)
        workers = max(1, min(context.max_workers, int(max(1.0, profile.worker_weight * context.max_workers))))
        rationale: List[str] = ["profile evaluated", f"cache_savings={cache_savings}"]
        if delay > 0:
            rationale.append("rate limit delay recommended")
        return ResourcePlan(
            provider=profile.provider,
            model=profile.model,
            workers=workers,
            request_batch_size=batch_size,
            estimated_tokens=effective_tokens,
            estimated_cost=round(profile.estimate_cost(effective_tokens), 6),
            cache_savings_tokens=cache_savings,
            rate_limit_delay_seconds=delay,
            rationale=rationale,
        )

    def rank(self, plans: Iterable[ResourcePlan]) -> List[ResourcePlan]:
        if self.prefer_low_cost:
            return sorted(plans, key=lambda item: (item.estimated_cost, item.rate_limit_delay_seconds, -item.workers))
        return sorted(plans, key=lambda item: (item.rate_limit_delay_seconds, -item.workers, item.estimated_cost))

# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Iterable

from .resource_result import ResourcePlan


def build_resource_metrics(plans: Iterable[ResourcePlan]) -> Dict[str, Any]:
    items = list(plans)
    if not items:
        return {"candidate_count": 0, "min_cost": 0.0, "max_workers": 0}
    costs = [plan.estimated_cost for plan in items]
    workers = [plan.workers for plan in items]
    return {
        "candidate_count": len(items),
        "min_cost": min(costs),
        "max_cost": max(costs),
        "max_workers": max(workers),
        "providers": sorted({plan.provider for plan in items}),
    }

# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from typing import Iterable

from .resource_context import ResourceContext
from .resource_optimizer import ResourceOptimizer
from .resource_profile import ResourceProfile
from .resource_result import ResourceOptimizationResult
from .workflow_context import WorkflowContext


def optimize_workflow_resources(
    workflow_context: WorkflowContext,
    profiles: Iterable[ResourceProfile] | None = None,
    optimizer: ResourceOptimizer | None = None,
) -> ResourceOptimizationResult:
    """Attach a Stage-17.3 resource plan to a Stage-17.1 workflow context."""

    optimizer = optimizer or ResourceOptimizer()
    context = ResourceContext.from_texts(
        [workflow_context.source_text],
        profiles=list(profiles or []),
        max_workers=int(workflow_context.metadata.get("max_workers", 4)),
        max_cost=workflow_context.metadata.get("max_cost"),
        cache_hit_rate=float(workflow_context.metadata.get("cache_hit_rate", 0.0)),
    )
    result = optimizer.optimize(context)
    workflow_context.artifacts["resource_plan"] = result.selected_plan.to_dict()
    workflow_context.record("resource_optimizer", provider=result.selected_plan.provider, workers=result.selected_plan.workers)
    return result

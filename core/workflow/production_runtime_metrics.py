# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Iterable


def build_production_runtime_metrics(workflow_result: Any, events: Iterable[Any], components: Dict[str, Any]) -> Dict[str, Any]:
    workflow_metrics: Dict[str, Any] = {}
    step_count = 0
    success = False
    if workflow_result is not None:
        workflow_metrics = dict(getattr(workflow_result, "metrics", {}) or {})
        step_count = len(getattr(workflow_result, "steps", []) or [])
        success = bool(getattr(workflow_result, "success", False))
    return {
        "stage": "Stage-17.7",
        "workflow_success": success,
        "workflow_step_count": step_count,
        "event_count": len(list(events)),
        "bound_components": sorted(name for name, value in components.items() if value is not None),
        "workflow_metrics": workflow_metrics,
    }

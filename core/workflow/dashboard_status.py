# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_result import DashboardStatus


def normalize_status(component: str, value) -> DashboardStatus:
    if isinstance(value, DashboardStatus):
        return value
    if isinstance(value, dict):
        return DashboardStatus(
            component=component,
            status=str(value.get("status", "unknown")),
            metrics=dict(value.get("metrics", {})),
            details={k: v for k, v in value.items() if k not in {"status", "metrics"}},
        )
    status = getattr(value, "status", None)
    metrics = getattr(value, "metrics", {})
    if status is not None:
        return DashboardStatus(component=component, status=str(status), metrics=dict(metrics or {}), details={"source_type": type(value).__name__})
    return DashboardStatus(component=component, status="unknown", details={"source_type": type(value).__name__})


def workflow_status(result=None) -> DashboardStatus:
    if result is None:
        return DashboardStatus("workflow", "idle")
    return normalize_status("workflow", result)


def job_status(result=None) -> DashboardStatus:
    if result is None:
        return DashboardStatus("job_scheduler", "idle", metrics={"jobs": 0})
    return normalize_status("job_scheduler", result)


def resource_status(result=None) -> DashboardStatus:
    if result is None:
        return DashboardStatus("resource_optimizer", "ready")
    return normalize_status("resource_optimizer", result)


def review_status(result=None) -> DashboardStatus:
    if result is None:
        return DashboardStatus("review_approval", "ready")
    return normalize_status("review_approval", result)


def export_status(result=None) -> DashboardStatus:
    if result is None:
        return DashboardStatus("export_framework", "ready")
    return normalize_status("export_framework", result)

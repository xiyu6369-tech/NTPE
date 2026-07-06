# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_result import DashboardStatus


def _number(value, default=0):
    return value if isinstance(value, (int, float)) else default


def build_dashboard_metrics(components: list[DashboardStatus]) -> dict:
    total = len(components)
    healthy = sum(1 for item in components if item.status in {"ok", "pass", "completed", "idle", "ready"})
    warning = sum(1 for item in components if item.status in {"warning", "degraded"})
    failed = sum(1 for item in components if item.status in {"fail", "failed", "error"})
    requests = sum(_number(item.metrics.get("requests")) for item in components)
    jobs = sum(_number(item.metrics.get("jobs")) for item in components)
    return {
        "components": total,
        "healthy_components": healthy,
        "warning_components": warning,
        "failed_components": failed,
        "total_requests": requests,
        "total_jobs": jobs,
        "health_ratio": 1.0 if total == 0 else round(healthy / total, 4),
    }

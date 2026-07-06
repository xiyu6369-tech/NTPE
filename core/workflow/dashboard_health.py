# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_result import DashboardStatus


def summarize_health(components: list[DashboardStatus]) -> str:
    if not components:
        return "unknown"
    statuses = {component.status for component in components}
    if statuses & {"fail", "failed", "error"}:
        return "degraded"
    if statuses & {"warning", "degraded"}:
        return "warning"
    return "ok"

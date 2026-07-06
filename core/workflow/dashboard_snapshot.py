# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_health import summarize_health
from .dashboard_metrics import build_dashboard_metrics
from .dashboard_result import DashboardSnapshot, DashboardStatus


def create_dashboard_snapshot(components: list[DashboardStatus]) -> DashboardSnapshot:
    metrics = build_dashboard_metrics(components)
    status = summarize_health(components)
    return DashboardSnapshot(status=status, components=list(components), metrics=metrics)

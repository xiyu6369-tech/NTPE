# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_api import MonitoringDashboardAPI
from .dashboard_status import normalize_status


def build_dashboard_snapshot(**components) -> dict:
    api = MonitoringDashboardAPI()
    for name, value in components.items():
        api.register_source(name, lambda name=name, value=value: normalize_status(name, value))
    return api.snapshot_dict()

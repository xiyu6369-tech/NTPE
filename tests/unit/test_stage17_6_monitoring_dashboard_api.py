from core.workflow.dashboard_api import MonitoringDashboardAPI
from core.workflow.dashboard_bridge import build_dashboard_snapshot
from core.workflow.dashboard_result import DashboardStatus


def test_dashboard_defaults_snapshot_passes():
    api = MonitoringDashboardAPI()
    api.register_defaults()
    snapshot = api.snapshot()
    assert snapshot.status == "ok"
    assert snapshot.metrics["components"] == 5
    assert api.component("workflow").status == "idle"


def test_dashboard_detects_degraded_component():
    api = MonitoringDashboardAPI()
    api.register_source("provider", lambda: DashboardStatus("provider", "failed", metrics={"requests": 3}))
    health = api.health()
    assert health["status"] == "degraded"
    assert health["metrics"]["failed_components"] == 1


def test_dashboard_bridge_normalizes_dicts():
    data = build_dashboard_snapshot(workflow={"status": "completed", "metrics": {"jobs": 2}})
    assert data["status"] == "ok"
    assert data["metrics"]["total_jobs"] == 2

# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API Launcher
# =====================================================

from core.workflow.dashboard_api import MonitoringDashboardAPI
from core.workflow.dashboard_result import DashboardStatus


def main() -> None:
    api = MonitoringDashboardAPI()
    api.register_defaults()
    api.register_source("provider_health", lambda: DashboardStatus("provider_health", "ok", metrics={"requests": 1}))
    snapshot = api.snapshot()
    assert snapshot.status == "ok"
    assert snapshot.metrics["components"] == 6
    assert api.health()["status"] == "ok"
    print("Stage-17.6 Launcher PASS")


if __name__ == "__main__":
    main()

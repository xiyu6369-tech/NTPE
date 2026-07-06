# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from .dashboard_events import (
    DASHBOARD_HEALTH_CHECKED,
    DASHBOARD_SNAPSHOT_CREATED,
    DASHBOARD_SOURCE_REGISTERED,
    DashboardEventBus,
)
from .dashboard_registry import DashboardRegistry
from .dashboard_result import DashboardSnapshot, DashboardStatus
from .dashboard_snapshot import create_dashboard_snapshot
from .dashboard_status import export_status, job_status, resource_status, review_status, workflow_status


class MonitoringDashboardAPI:
    """Shared monitoring API for CLI, GUI, Web UI, and automation layers."""

    stage = "Stage-17.6"
    name = "Monitoring Dashboard API"

    def __init__(self, registry: DashboardRegistry | None = None, event_bus: DashboardEventBus | None = None) -> None:
        self.registry = registry or DashboardRegistry()
        self.events = event_bus or DashboardEventBus()
        self._last_snapshot: DashboardSnapshot | None = None

    def register_source(self, name: str, source) -> None:
        self.registry.register(name, source)
        self.events.emit(DASHBOARD_SOURCE_REGISTERED, source=name)

    def register_defaults(self) -> None:
        defaults = {
            "workflow": workflow_status,
            "job_scheduler": job_status,
            "resource_optimizer": resource_status,
            "review_approval": review_status,
            "export_framework": export_status,
        }
        for name, source in defaults.items():
            if name not in self.registry.names():
                self.register_source(name, source)

    def snapshot(self) -> DashboardSnapshot:
        components = self.registry.collect()
        snapshot = create_dashboard_snapshot(components)
        self._last_snapshot = snapshot
        self.events.emit(DASHBOARD_SNAPSHOT_CREATED, status=snapshot.status, components=len(snapshot.components))
        return snapshot

    def snapshot_dict(self) -> dict:
        return self.snapshot().to_dict()

    def health(self) -> dict:
        snapshot = self.snapshot()
        result = {"status": snapshot.status, "metrics": dict(snapshot.metrics)}
        self.events.emit(DASHBOARD_HEALTH_CHECKED, status=snapshot.status)
        return result

    def component(self, name: str) -> DashboardStatus | None:
        snapshot = self._last_snapshot or self.snapshot()
        for component in snapshot.components:
            if component.component == name:
                return component
        return None

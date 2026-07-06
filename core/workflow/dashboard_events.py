# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

DASHBOARD_SNAPSHOT_CREATED = "DashboardSnapshotCreated"
DASHBOARD_SOURCE_REGISTERED = "DashboardSourceRegistered"
DASHBOARD_HEALTH_CHECKED = "DashboardHealthChecked"


@dataclass(frozen=True)
class DashboardEvent:
    name: str
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DashboardEventBus:
    def __init__(self) -> None:
        self.events: list[DashboardEvent] = []

    def emit(self, name: str, **payload) -> DashboardEvent:
        event = DashboardEvent(name=name, payload=dict(payload))
        self.events.append(event)
        return event

    def latest(self, limit: int = 20) -> list[DashboardEvent]:
        return self.events[-max(0, limit):]

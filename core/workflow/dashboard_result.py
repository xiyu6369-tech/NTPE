# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DashboardStatus:
    component: str
    status: str = "unknown"
    metrics: dict = field(default_factory=dict)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "status": self.status,
            "metrics": dict(self.metrics),
            "details": dict(self.details),
        }


@dataclass
class DashboardSnapshot:
    status: str
    components: list[DashboardStatus] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "metrics": dict(self.metrics),
            "components": [component.to_dict() for component in self.components],
        }

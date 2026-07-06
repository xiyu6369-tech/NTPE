# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

from __future__ import annotations

from collections.abc import Callable

from .dashboard_result import DashboardStatus

DashboardSource = Callable[[], DashboardStatus]


class DashboardRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, DashboardSource] = {}

    def register(self, name: str, source: DashboardSource) -> None:
        if not name:
            raise ValueError("dashboard source name is required")
        self._sources[name] = source

    def unregister(self, name: str) -> None:
        self._sources.pop(name, None)

    def names(self) -> list[str]:
        return sorted(self._sources)

    def collect(self) -> list[DashboardStatus]:
        return [source() for _, source in sorted(self._sources.items())]

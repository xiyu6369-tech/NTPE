from __future__ import annotations

from typing import Any, Dict, Mapping


class DashboardBuilder:
    def build(self, report: Mapping[str, Any], regression: Mapping[str, Any] | None = None, trend: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "schema": "ntpe.performance.dashboard.v1",
            "title": report.get("title", "NTPE Performance Dashboard"),
            "status": (report.get("summary") or {}).get("status", "UNKNOWN"),
            "summary": dict(report.get("summary") or {}),
            "categories": dict(report.get("categories") or {}),
            "regression": dict(regression or {}),
            "trend": dict(trend or {}),
        }


def build_dashboard(report: Mapping[str, Any], regression: Mapping[str, Any] | None = None, trend: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return DashboardBuilder().build(report, regression, trend)

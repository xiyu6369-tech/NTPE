"""Framework-neutral dashboard builder for NTPE Stage-13.2."""
from __future__ import annotations

from typing import Any, Dict

from .dashboard_models import DashboardMetric, DashboardSection, DashboardView
from .ui_models import WebUiState


class WebUiDashboard:
    """Builds dashboard data from WebUiState without touching runtime internals."""

    stage = "13.2"

    def build(self, state: WebUiState) -> DashboardView:
        state_data = state.to_dict()
        health: Dict[str, Any] = dict(state_data.get("health") or {})
        metadata: Dict[str, Any] = dict(state_data.get("metadata") or {})

        status_code = health.get("status_code")
        rest_available = bool(state_data.get("rest_api_available"))
        api_status = "healthy" if rest_available else "critical"

        metrics = [
            DashboardMetric("rest_api", "REST API", "available" if rest_available else "unavailable", api_status),
            DashboardMetric("runtime_api_stage", "Runtime API", state_data.get("runtime_api_stage") or "unknown", "normal"),
            DashboardMetric("external_api_stage", "External API", state_data.get("external_api_stage") or "unknown", "normal"),
            DashboardMetric("route_count", "REST Routes", metadata.get("route_count", 0), "normal"),
        ]

        sections = [
            DashboardSection(
                "system_status",
                "System Status",
                items=[
                    {"label": "REST status code", "value": status_code},
                    {"label": "Uses External API only", "value": metadata.get("uses_external_api_only")},
                    {"label": "Uses Frozen Runtime API only", "value": metadata.get("uses_frozen_runtime_api_only")},
                ],
            ),
            DashboardSection(
                "translation_guard",
                "Translation Guard",
                items=[
                    {"label": "Runtime boundary", "value": "frozen runtime API"},
                    {"label": "External boundary", "value": "frozen REST API"},
                    {"label": "Core translation path", "value": "unchanged"},
                ],
                metadata={"validation_stage": self.stage},
            ),
        ]

        return DashboardView(
            metrics=metrics,
            sections=sections,
            metadata={
                "framework_neutral": True,
                "uses_web_ui_state_only": True,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState) -> Dict[str, Any]:
        view = self.build(state).to_dict()
        return {
            "stage": self.stage,
            "metric_count": len(view["metrics"]),
            "section_count": len(view["sections"]),
            "rest_api_available": state.rest_api_available,
            "framework_neutral": True,
        }

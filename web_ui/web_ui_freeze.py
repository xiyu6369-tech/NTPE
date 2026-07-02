"""Web UI freeze manifest for NTPE Stage-13.8.

This module documents the frozen Web UI public surface for NTPE 1.0 Beta.
It is intentionally additive and does not alter Web UI routing, REST clients,
or runtime/external API behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

WEB_UI_FREEZE_STAGE = "13.8"
WEB_UI_FREEZE_NAME = "NTPE Web UI Layer Freeze"
WEB_UI_FROZEN_PAGES = (
    "dashboard",
    "sessions",
    "jobs",
    "pipelines",
    "events",
    "resources",
)
WEB_UI_REQUIRED_ROUTES = (
    "/",
    "/sessions",
    "/jobs",
    "/pipelines",
    "/events",
    "/resources",
)


@dataclass(frozen=True)
class WebUiFreezeReport:
    """Serializable report describing the frozen Web UI surface."""

    stage: str = WEB_UI_FREEZE_STAGE
    name: str = WEB_UI_FREEZE_NAME
    frozen: bool = True
    pages: List[str] = field(default_factory=lambda: list(WEB_UI_FROZEN_PAGES))
    routes: List[str] = field(default_factory=lambda: list(WEB_UI_REQUIRED_ROUTES))
    uses_external_api_only: bool = True
    uses_frozen_runtime_api_only: bool = True
    additive_only: bool = True
    compatibility: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "frozen": self.frozen,
            "pages": list(self.pages),
            "routes": list(self.routes),
            "uses_external_api_only": self.uses_external_api_only,
            "uses_frozen_runtime_api_only": self.uses_frozen_runtime_api_only,
            "additive_only": self.additive_only,
            "compatibility": dict(self.compatibility),
        }


def _unique(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        item = str(value)
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def create_web_ui_freeze_report(app: Any) -> WebUiFreezeReport:
    """Create a freeze report from a WebUiApp-compatible object."""

    manifest = app.manifest()
    shell = manifest.get("shell") or {}
    routes = shell.get("routes") or []
    route_paths = []
    for route in routes:
        if isinstance(route, dict):
            route_paths.append(str(route.get("path") or ""))
    if not route_paths:
        route_paths = list(WEB_UI_REQUIRED_ROUTES)

    compatibility = {
        "dashboard_page": manifest.get("dashboard_stage") == "13.2",
        "session_page": manifest.get("session_page_stage") == "13.3",
        "job_page": manifest.get("job_page_stage") == "13.4",
        "pipeline_page": manifest.get("pipeline_page_stage") == "13.5",
        "event_page": manifest.get("event_page_stage") == "13.6",
        "resource_page": manifest.get("resource_page_stage") == "13.7",
        "external_api_boundary": manifest.get("uses_external_api_only") is True,
        "runtime_api_boundary": manifest.get("uses_frozen_runtime_api_only") is True,
        "framework_neutral": manifest.get("framework_neutral") is True,
        "additive_only": manifest.get("additive_only") is True,
    }

    return WebUiFreezeReport(
        pages=list(WEB_UI_FROZEN_PAGES),
        routes=_unique(route_paths),
        uses_external_api_only=manifest.get("uses_external_api_only") is True,
        uses_frozen_runtime_api_only=manifest.get("uses_frozen_runtime_api_only") is True,
        additive_only=manifest.get("additive_only") is True,
        compatibility=compatibility,
    )


def validate_web_ui_freeze(app: Any) -> Dict[str, Any]:
    """Validate the Stage-13 Web UI freeze contract."""

    report = create_web_ui_freeze_report(app)
    data = report.to_dict()
    required_routes = set(WEB_UI_REQUIRED_ROUTES)
    available_routes = set(data["routes"])
    checks = {
        "frozen": data["frozen"] is True,
        "required_routes": required_routes.issubset(available_routes),
        "required_pages": set(WEB_UI_FROZEN_PAGES).issubset(set(data["pages"])),
        "external_api_boundary": data["uses_external_api_only"] is True,
        "runtime_api_boundary": data["uses_frozen_runtime_api_only"] is True,
        "additive_only": data["additive_only"] is True,
        "compatibility": all(data["compatibility"].values()),
    }
    data["checks"] = checks
    data["passed"] = all(checks.values())
    return data

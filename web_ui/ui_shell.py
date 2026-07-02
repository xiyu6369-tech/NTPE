"""Framework-neutral Web UI shell for NTPE Stage-13.1."""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from .ui_models import WEB_UI_STAGE, WEB_UI_VERSION, WebUiPage, WebUiRoute, WebUiState


class WebUiShell:
    """Minimal UI shell that owns navigation and page rendering metadata."""

    version = WEB_UI_VERSION
    stage = WEB_UI_STAGE

    def __init__(self, routes: Optional[Iterable[WebUiRoute]] = None) -> None:
        self._routes: Dict[str, WebUiRoute] = {}
        self._register_default_routes()
        for route in routes or ():
            self.register_route(route)

    def _register_default_routes(self) -> None:
        self.register_route(WebUiRoute("/", "Dashboard", "dashboard"))
        self.register_route(WebUiRoute("/sessions", "Sessions", "sessions"))
        self.register_route(WebUiRoute("/jobs", "Jobs", "jobs"))
        self.register_route(WebUiRoute("/pipelines", "Pipelines", "pipelines"))
        self.register_route(WebUiRoute("/events", "Events", "events"))
        self.register_route(WebUiRoute("/resources", "Resources", "resources"))
        self.register_route(WebUiRoute("/settings", "Settings", "settings"))

    def register_route(self, route: WebUiRoute) -> "WebUiShell":
        if not isinstance(route, WebUiRoute):
            raise TypeError("route must be a WebUiRoute")
        self._routes[route.path] = route
        return self

    def route(self, path: str) -> Optional[WebUiRoute]:
        normalized = path if str(path).startswith("/") else f"/{path}"
        return self._routes.get(normalized)

    def routes(self) -> tuple[WebUiRoute, ...]:
        return tuple(self._routes[path] for path in sorted(self._routes))

    def navigation(self) -> list[dict]:
        return [route.to_dict() for route in self.routes() if route.navigation]

    def render_page(self, path: str, state: WebUiState) -> WebUiPage:
        route = self.route(path)
        if route is None:
            route = WebUiRoute(path, "Not Found", "not_found", navigation=False, metadata={"not_found": True})
        components = [
            {"type": "navigation", "items": self.navigation()},
            {"type": "page_header", "title": route.title, "page_id": route.page_id},
            {"type": "status_panel", "state": state.to_dict()},
        ]
        return WebUiPage(route=route, state=state, components=components)

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "routes": [route.to_dict() for route in self.routes()],
            "framework_neutral": True,
            "additive_only": True,
        }

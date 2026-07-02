"""NTPE Stage-13.1 Web UI application facade."""
from __future__ import annotations

from typing import Optional

from external_api import RestApi

from .rest_client import WebUiRestClient
from .dashboard import WebUiDashboard
from .session_page import WebUiSessionPage
from .job_page import WebUiJobPage
from .pipeline_page import WebUiPipelinePage
from .event_page import WebUiEventPage
from .ui_models import WEB_UI_STAGE, WEB_UI_VERSION, WebUiPage
from .ui_shell import WebUiShell


class WebUiApp:
    """Framework-neutral application facade for future Web UI frontends."""

    version = WEB_UI_VERSION
    stage = WEB_UI_STAGE

    def __init__(self, rest_api: Optional[RestApi] = None) -> None:
        self.client = WebUiRestClient(rest_api=rest_api)
        self.shell = WebUiShell()
        self.dashboard = WebUiDashboard()
        self.session_page = WebUiSessionPage(self.client)
        self.job_page = WebUiJobPage(self.client)
        self.pipeline_page = WebUiPipelinePage(self.client)
        self.event_page = WebUiEventPage(self.client)

    def render(self, path: str = "/") -> WebUiPage:
        state = self.client.state()
        page = self.shell.render_page(path, state)
        if page.route.page_id == "dashboard":
            components = list(page.components)
            components.append({"type": "dashboard", "view": self.dashboard.build(state).to_dict()})
            return WebUiPage(route=page.route, state=page.state, components=components, created_at=page.created_at)
        if page.route.page_id == "sessions":
            components = list(page.components)
            components.append({"type": "session_page", "view": self.session_page.build(state).to_dict()})
            return WebUiPage(route=page.route, state=page.state, components=components, created_at=page.created_at)
        if page.route.page_id == "jobs":
            components = list(page.components)
            components.append({"type": "job_page", "view": self.job_page.build(state).to_dict()})
            return WebUiPage(route=page.route, state=page.state, components=components, created_at=page.created_at)
        if page.route.page_id == "pipelines":
            components = list(page.components)
            components.append({"type": "pipeline_page", "view": self.pipeline_page.build(state).to_dict()})
            return WebUiPage(route=page.route, state=page.state, components=components, created_at=page.created_at)
        if page.route.page_id == "events":
            components = list(page.components)
            components.append({"type": "event_page", "view": self.event_page.build(state).to_dict()})
            return WebUiPage(route=page.route, state=page.state, components=components, created_at=page.created_at)
        return page

    def dashboard_view(self) -> dict:
        return self.dashboard.build(self.client.state()).to_dict()

    def session_view(self) -> dict:
        state = self.client.state()
        return self.session_page.build(state).to_dict()

    def job_view(self) -> dict:
        state = self.client.state()
        return self.job_page.build(state).to_dict()

    def pipeline_view(self) -> dict:
        state = self.client.state()
        return self.pipeline_page.build(state).to_dict()

    def event_view(self) -> dict:
        state = self.client.state()
        return self.event_page.build(state).to_dict()

    def manifest(self) -> dict:
        rest_manifest = self.client.manifest()
        return {
            "version": self.version,
            "stage": self.stage,
            "shell": self.shell.manifest(),
            "external_api_stage": rest_manifest.get("stage"),
            "runtime_api_stage": rest_manifest.get("runtime_api_stage"),
            "uses_external_api_only": True,
            "uses_frozen_runtime_api_only": rest_manifest.get("uses_frozen_runtime_api_only"),
            "framework_neutral": True,
            "dashboard_stage": self.dashboard.stage,
            "session_page_stage": self.session_page.stage,
            "job_page_stage": self.job_page.stage,
            "pipeline_page_stage": self.pipeline_page.stage,
            "event_page_stage": self.event_page.stage,
            "additive_only": True,
        }


def create_web_ui_app(rest_api: Optional[RestApi] = None) -> WebUiApp:
    return WebUiApp(rest_api=rest_api)

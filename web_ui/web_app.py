"""NTPE Stage-13.1 Web UI application facade."""
from __future__ import annotations

from typing import Optional

from external_api import RestApi

from .rest_client import WebUiRestClient
from .ui_models import WEB_UI_STAGE, WEB_UI_VERSION, WebUiPage
from .ui_shell import WebUiShell


class WebUiApp:
    """Framework-neutral application facade for future Web UI frontends."""

    version = WEB_UI_VERSION
    stage = WEB_UI_STAGE

    def __init__(self, rest_api: Optional[RestApi] = None) -> None:
        self.client = WebUiRestClient(rest_api=rest_api)
        self.shell = WebUiShell()

    def render(self, path: str = "/") -> WebUiPage:
        return self.shell.render_page(path, self.client.state())

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
            "additive_only": True,
        }


def create_web_ui_app(rest_api: Optional[RestApi] = None) -> WebUiApp:
    return WebUiApp(rest_api=rest_api)

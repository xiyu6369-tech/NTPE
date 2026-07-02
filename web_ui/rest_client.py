"""REST-backed UI adapter for NTPE Stage-13.1."""
from __future__ import annotations

from typing import Any, Dict, Optional

from external_api import RestApi, create_rest_api

from .ui_models import WebUiState


class WebUiRestClient:
    """Small adapter that lets UI code talk only to the frozen REST surface."""

    def __init__(self, rest_api: Optional[RestApi] = None) -> None:
        self.rest_api = rest_api or create_rest_api()

    def health(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/health")
        return response.to_dict()

    def manifest(self) -> Dict[str, Any]:
        return self.rest_api.manifest()

    def state(self) -> WebUiState:
        manifest = self.manifest()
        health = self.health()
        return WebUiState(
            rest_api_available=health.get("status_code") == 200,
            runtime_api_stage=manifest.get("runtime_api_stage"),
            external_api_stage=manifest.get("stage"),
            health=health,
            metadata={
                "uses_external_api_only": True,
                "uses_frozen_runtime_api_only": manifest.get("uses_frozen_runtime_api_only"),
                "route_count": len(manifest.get("routes", [])),
            },
        )

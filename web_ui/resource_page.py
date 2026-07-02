"""Framework-neutral Web UI resource page for NTPE Stage-13.7."""
from __future__ import annotations

from typing import Any, Dict, List

from .resource_models import ResourceAction, ResourcePageView, WEB_UI_RESOURCE_STAGE
from .rest_client import WebUiRestClient
from .ui_models import WebUiState


class WebUiResourcePage:
    """Builds the resource page using only REST Resource API responses."""

    stage = WEB_UI_RESOURCE_STAGE

    def __init__(self, client: WebUiRestClient | None = None) -> None:
        self.client = client

    def _client(self, client: WebUiRestClient | None = None) -> WebUiRestClient:
        active = client or self.client
        if active is None:
            raise ValueError("WebUiResourcePage requires a WebUiRestClient")
        return active

    def actions(self) -> List[ResourceAction]:
        return [
            ResourceAction("create", "Create Resource", "POST", "/v1/resources"),
            ResourceAction("refresh", "Refresh Resources", "GET", "/v1/resources"),
            ResourceAction("detail", "Open Detail", "GET", "/v1/resources/{resource_id}"),
            ResourceAction("filter", "Filter Resources", "POST", "/v1/resources/filter"),
            ResourceAction("reserve", "Reserve Resource", "POST", "/v1/resources/{resource_id}/reserve"),
            ResourceAction("attach", "Attach Resource", "POST", "/v1/resources/{resource_id}/attach"),
            ResourceAction("release", "Release Resource", "POST", "/v1/resources/{resource_id}/release"),
            ResourceAction("summary", "Summary", "GET", "/v1/resources/summary"),
        ]

    def build(self, state: WebUiState, client: WebUiRestClient | None = None) -> ResourcePageView:
        active_client = self._client(client)
        resource_response = active_client.list_resources()
        body: Dict[str, Any] = dict(resource_response.get("body") or {})
        data: Dict[str, Any] = dict(body.get("data") or {})
        resources = data.get("resources") or data.get("items") or []
        if not isinstance(resources, list):
            resources = []

        summary_response = active_client.resource_summary()
        summary_body: Dict[str, Any] = dict(summary_response.get("body") or {})
        summary_data = summary_body.get("data") or {}
        if not isinstance(summary_data, dict):
            summary_data = {}

        return ResourcePageView(
            resources=[dict(resource) for resource in resources if isinstance(resource, dict)],
            actions=self.actions(),
            summary=dict(summary_data),
            metadata={
                "rest_status_code": resource_response.get("status_code"),
                "summary_status_code": summary_response.get("status_code"),
                "uses_rest_resource_api_only": True,
                "uses_frozen_runtime_api_only": state.metadata.get("uses_frozen_runtime_api_only"),
                "rest_api_available": state.rest_api_available,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState, client: WebUiRestClient | None = None) -> Dict[str, Any]:
        view = self.build(state, client).to_dict()
        return {
            "stage": self.stage,
            "resource_count": len(view["resources"]),
            "action_count": len(view["actions"]),
            "rest_api_available": state.rest_api_available,
            "uses_rest_resource_api_only": view["metadata"].get("uses_rest_resource_api_only"),
        }

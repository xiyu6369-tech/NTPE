"""Framework-neutral Web UI event page for NTPE Stage-13.6."""
from __future__ import annotations

from typing import Any, Dict, List

from .event_models import EventAction, EventPageView, WEB_UI_EVENT_STAGE
from .rest_client import WebUiRestClient
from .ui_models import WebUiState


class WebUiEventPage:
    """Builds the event page using only REST Event API responses."""

    stage = WEB_UI_EVENT_STAGE

    def __init__(self, client: WebUiRestClient | None = None) -> None:
        self.client = client

    def _client(self, client: WebUiRestClient | None = None) -> WebUiRestClient:
        active = client or self.client
        if active is None:
            raise ValueError("WebUiEventPage requires a WebUiRestClient")
        return active

    def actions(self) -> List[EventAction]:
        return [
            EventAction("publish", "Publish Event", "POST", "/v1/events"),
            EventAction("refresh", "Refresh Events", "GET", "/v1/events"),
            EventAction("detail", "Open Detail", "GET", "/v1/events/{event_id}"),
            EventAction("filter", "Filter Events", "POST", "/v1/events/filter"),
            EventAction("summary", "Summary", "GET", "/v1/events/summary"),
            EventAction("clear", "Clear Events", "POST", "/v1/events/clear"),
        ]

    def build(self, state: WebUiState, client: WebUiRestClient | None = None) -> EventPageView:
        active_client = self._client(client)
        event_response = active_client.list_events()
        body: Dict[str, Any] = dict(event_response.get("body") or {})
        data: Dict[str, Any] = dict(body.get("data") or {})
        events = data.get("events") or data.get("items") or []
        if not isinstance(events, list):
            events = []

        summary_response = active_client.event_summary()
        summary_body: Dict[str, Any] = dict(summary_response.get("body") or {})
        summary_data = summary_body.get("data") or {}
        if not isinstance(summary_data, dict):
            summary_data = {}

        return EventPageView(
            events=[dict(event) for event in events if isinstance(event, dict)],
            actions=self.actions(),
            summary=dict(summary_data),
            metadata={
                "rest_status_code": event_response.get("status_code"),
                "summary_status_code": summary_response.get("status_code"),
                "uses_rest_event_api_only": True,
                "uses_frozen_runtime_api_only": state.metadata.get("uses_frozen_runtime_api_only"),
                "rest_api_available": state.rest_api_available,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState, client: WebUiRestClient | None = None) -> Dict[str, Any]:
        view = self.build(state, client).to_dict()
        return {
            "stage": self.stage,
            "event_count": len(view["events"]),
            "action_count": len(view["actions"]),
            "rest_api_available": state.rest_api_available,
            "uses_rest_event_api_only": view["metadata"].get("uses_rest_event_api_only"),
        }

"""Framework-neutral Web UI session page for NTPE Stage-13.3."""
from __future__ import annotations

from typing import Any, Dict, List

from .rest_client import WebUiRestClient
from .session_models import SessionAction, SessionPageView, WEB_UI_SESSION_STAGE
from .ui_models import WebUiState


class WebUiSessionPage:
    """Builds the session page using only REST Session API responses."""

    stage = WEB_UI_SESSION_STAGE

    def __init__(self, client: WebUiRestClient | None = None) -> None:
        self.client = client

    def _client(self, client: WebUiRestClient | None = None) -> WebUiRestClient:
        active = client or self.client
        if active is None:
            raise ValueError("WebUiSessionPage requires a WebUiRestClient")
        return active

    def actions(self) -> List[SessionAction]:
        return [
            SessionAction("create", "Create Session", "POST", "/v1/sessions"),
            SessionAction("refresh", "Refresh Sessions", "GET", "/v1/sessions"),
            SessionAction("activate", "Activate", "POST", "/v1/sessions/{session_id}/activate"),
            SessionAction("pause", "Pause", "POST", "/v1/sessions/{session_id}/pause"),
            SessionAction("complete", "Complete", "POST", "/v1/sessions/{session_id}/complete"),
            SessionAction("cancel", "Cancel", "POST", "/v1/sessions/{session_id}/cancel"),
            SessionAction("resume_state", "Resume State", "GET", "/v1/sessions/{session_id}/resume-state"),
        ]

    def build(self, state: WebUiState, client: WebUiRestClient | None = None) -> SessionPageView:
        active_client = self._client(client)
        session_response = active_client.list_sessions()
        body: Dict[str, Any] = dict(session_response.get("body") or {})
        data: Dict[str, Any] = dict(body.get("data") or {})
        sessions = data.get("sessions") or data.get("items") or []
        if not isinstance(sessions, list):
            sessions = []

        return SessionPageView(
            sessions=[dict(session) for session in sessions if isinstance(session, dict)],
            actions=self.actions(),
            metadata={
                "rest_status_code": session_response.get("status_code"),
                "uses_rest_session_api_only": True,
                "uses_frozen_runtime_api_only": state.metadata.get("uses_frozen_runtime_api_only"),
                "rest_api_available": state.rest_api_available,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState, client: WebUiRestClient | None = None) -> Dict[str, Any]:
        view = self.build(state, client).to_dict()
        return {
            "stage": self.stage,
            "session_count": len(view["sessions"]),
            "action_count": len(view["actions"]),
            "rest_api_available": state.rest_api_available,
            "uses_rest_session_api_only": view["metadata"].get("uses_rest_session_api_only"),
        }

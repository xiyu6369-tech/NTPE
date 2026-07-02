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


    def list_sessions(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/sessions")
        return response.to_dict()

    def create_session(self, name: str | None = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"name": name, "metadata": dict(metadata or {})}
        response = self.rest_api.handle("POST", "/v1/sessions", body=body)
        return response.to_dict()

    def session_action(self, session_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        method = "GET" if action == "resume-state" else "POST"
        body = {} if method == "GET" else {"metadata": dict(metadata or {})}
        response = self.rest_api.handle(method, f"/v1/sessions/{session_id}/{action}", body=body)
        return response.to_dict()


    def list_jobs(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/jobs")
        return response.to_dict()

    def create_job(self, session_id: str | None = None, name: str | None = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"session_id": session_id, "name": name, "metadata": dict(metadata or {})}
        response = self.rest_api.handle("POST", "/v1/jobs", body=body)
        return response.to_dict()

    def job_action(self, job_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        method = "GET" if action in {"status", "result"} else "POST"
        body = {} if method == "GET" else {"metadata": dict(metadata or {})}
        response = self.rest_api.handle(method, f"/v1/jobs/{job_id}/{action}", body=body)
        return response.to_dict()



    def list_pipelines(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/pipelines")
        return response.to_dict()

    def create_pipeline(self, name: str | None = None, stages: Optional[list[Dict[str, Any]]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"name": name, "stages": list(stages or []), "metadata": dict(metadata or {})}
        response = self.rest_api.handle("POST", "/v1/pipelines", body=body)
        return response.to_dict()

    def pipeline_action(self, pipeline_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        method = "GET" if action in {"status", "summary"} else "POST"
        body = {} if method == "GET" else {"metadata": dict(metadata or {})}
        response = self.rest_api.handle(method, f"/v1/pipelines/{pipeline_id}/{action}", body=body)
        return response.to_dict()



    def list_events(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/events")
        return response.to_dict()

    def publish_event(self, name: str | None = None, event_type: str = "custom", severity: str = "info", message: str | None = None, payload: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {
            "name": name or "runtime.event",
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "payload": dict(payload or {}),
            "metadata": dict(metadata or {}),
        }
        response = self.rest_api.handle("POST", "/v1/events", body=body)
        return response.to_dict()

    def filter_events(self, **filters: Any) -> Dict[str, Any]:
        response = self.rest_api.handle("POST", "/v1/events/filter", body={k: v for k, v in filters.items() if v is not None})
        return response.to_dict()

    def event_summary(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/events/summary")
        return response.to_dict()

    def clear_events(self) -> Dict[str, Any]:
        response = self.rest_api.handle("POST", "/v1/events/clear")
        return response.to_dict()


    def list_resources(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/resources")
        return response.to_dict()

    def create_resource(self, name: str | None = None, resource_type: str = "custom", uri: str | None = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"name": name, "resource_type": resource_type, "uri": uri, "metadata": dict(metadata or {})}
        response = self.rest_api.handle("POST", "/v1/resources", body=body)
        return response.to_dict()

    def filter_resources(self, **filters: Any) -> Dict[str, Any]:
        response = self.rest_api.handle("POST", "/v1/resources/filter", body={k: v for k, v in filters.items() if v is not None})
        return response.to_dict()

    def resource_action(self, resource_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        method = "GET" if action == "summary" else "POST"
        body = {} if method == "GET" else {"metadata": dict(metadata or {})}
        response = self.rest_api.handle(method, f"/v1/resources/{resource_id}/{action}", body=body)
        return response.to_dict()

    def resource_summary(self) -> Dict[str, Any]:
        response = self.rest_api.handle("GET", "/v1/resources/summary")
        return response.to_dict()

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

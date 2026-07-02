"""External API / REST freeze contract for NTPE 1.0 Beta Stage-12.8.

This module is additive. It records and validates the public External API / REST
surface introduced during Stage-12.1 through Stage-12.7. It does not modify REST
routing behavior, Runtime API behavior, Platform Services, Workflow, SDK, CLI, or
Foundation contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Tuple

EXTERNAL_API_FREEZE_STAGE = "12.8"
EXTERNAL_API_FREEZE_NAME = "External API Freeze"
EXTERNAL_API_FREEZE_VERSION = "1.0.0-beta.12.8"

FROZEN_EXTERNAL_API_MODULES: Tuple[str, ...] = (
    "external_api.rest_models",
    "external_api.rest_router",
    "external_api.rest_api",
    "external_api.rest_session",
    "external_api.rest_job",
    "external_api.rest_pipeline",
    "external_api.rest_event",
    "external_api.rest_resource",
    "external_api.rest_middleware",
    "external_api.rest_auth",
)

FROZEN_EXTERNAL_API_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("GET", "/health"),
    ("GET", "/v1/runtime/manifest"),
    ("POST", "/v1/runtime/execute"),
    ("POST", "/v1/sessions"),
    ("GET", "/v1/sessions"),
    ("POST", "/v1/jobs"),
    ("GET", "/v1/jobs"),
    ("POST", "/v1/pipelines"),
    ("GET", "/v1/pipelines"),
    ("POST", "/v1/events"),
    ("GET", "/v1/events"),
    ("GET", "/v1/events/summary"),
    ("POST", "/v1/events/filter"),
    ("POST", "/v1/events/clear"),
    ("POST", "/v1/resources"),
    ("GET", "/v1/resources"),
    ("GET", "/v1/resources/summary"),
    ("POST", "/v1/resources/filter"),
)

FROZEN_EXTERNAL_API_DYNAMIC_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("GET", "/v1/sessions/{session_id}"),
    ("POST", "/v1/sessions/{session_id}/activate"),
    ("POST", "/v1/sessions/{session_id}/pause"),
    ("POST", "/v1/sessions/{session_id}/complete"),
    ("POST", "/v1/sessions/{session_id}/fail"),
    ("POST", "/v1/sessions/{session_id}/cancel"),
    ("GET", "/v1/sessions/{session_id}/resume-state"),
    ("GET", "/v1/jobs/{job_id}"),
    ("POST", "/v1/jobs/{job_id}/start"),
    ("POST", "/v1/jobs/{job_id}/stop"),
    ("POST", "/v1/jobs/{job_id}/cancel"),
    ("POST", "/v1/jobs/{job_id}/resume"),
    ("GET", "/v1/jobs/{job_id}/result"),
    ("GET", "/v1/pipelines/{pipeline_id}"),
    ("POST", "/v1/pipelines/{pipeline_id}/start"),
    ("POST", "/v1/pipelines/{pipeline_id}/complete"),
    ("GET", "/v1/events/{event_id}"),
    ("GET", "/v1/resources/{resource_id}"),
    ("POST", "/v1/resources/{resource_id}/transition"),
    ("POST", "/v1/resources/{resource_id}/release"),
)

FROZEN_EXTERNAL_API_SURFACES: Tuple[str, ...] = (
    "REST Core",
    "REST Session API",
    "REST Job API",
    "REST Pipeline API",
    "REST Event API",
    "REST Resource API",
    "REST Middleware",
    "REST Auth Hooks",
)

FROZEN_EXTERNAL_API_COMPATIBILITY: Tuple[str, ...] = (
    "Foundation v1.0",
    "CLI",
    "SDK",
    "Integration",
    "Workflow",
    "Platform Services",
    "Runtime API",
    "External API",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ExternalApiFreezeReport:
    """Serializable External API freeze validation report."""

    stage: str = EXTERNAL_API_FREEZE_STAGE
    version: str = EXTERNAL_API_FREEZE_VERSION
    name: str = EXTERNAL_API_FREEZE_NAME
    modules: Tuple[str, ...] = FROZEN_EXTERNAL_API_MODULES
    routes: Tuple[Tuple[str, str], ...] = FROZEN_EXTERNAL_API_ROUTES
    surfaces: Tuple[str, ...] = FROZEN_EXTERNAL_API_SURFACES
    compatibility_surfaces: Tuple[str, ...] = FROZEN_EXTERNAL_API_COMPATIBILITY
    frozen: bool = True
    additive_only: bool = True
    uses_frozen_runtime_api_only: bool = True
    created_at: str = field(default_factory=_utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "name": self.name,
            "modules": list(self.modules),
            "routes": [{"method": method, "path": path} for method, path in self.routes],
            "dynamic_routes": [{"method": method, "path": path} for method, path in FROZEN_EXTERNAL_API_DYNAMIC_ROUTES],
            "surfaces": list(self.surfaces),
            "compatibility_surfaces": list(self.compatibility_surfaces),
            "frozen": self.frozen,
            "additive_only": self.additive_only,
            "uses_frozen_runtime_api_only": self.uses_frozen_runtime_api_only,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class ExternalApiFreezeValidator:
    """Validates that the Stage-12 External API public surface is present."""

    def __init__(self, *, required_routes: Iterable[Tuple[str, str]] | None = None) -> None:
        self.required_routes = tuple(required_routes or FROZEN_EXTERNAL_API_ROUTES)

    def report(self, **metadata: Any) -> ExternalApiFreezeReport:
        return ExternalApiFreezeReport(metadata=dict(metadata or {}))

    def validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        route_pairs = {(str(route.get("method", "")).upper(), str(route.get("path", ""))) for route in manifest.get("routes", [])}
        required_exact = {(method, path) for method, path in self.required_routes if "{" not in path}
        if not required_exact.issubset(route_pairs):
            return False
        return (
            manifest.get("uses_frozen_runtime_api_only") is True
            and manifest.get("additive_only") is True
            and "session_api" in manifest
            and "job_api" in manifest
            and "pipeline_api" in manifest
            and "event_api" in manifest
            and "resource_api" in manifest
            and "middleware_api" in manifest
            and "auth_hooks" in manifest
        )

    def validate_rest_api(self, api: Any) -> ExternalApiFreezeReport:
        if not hasattr(api, "manifest"):
            raise AssertionError("REST API object does not expose manifest()")
        manifest = api.manifest()
        if not self.validate_manifest(manifest):
            raise AssertionError("External API manifest does not satisfy freeze contract")
        response = api.handle("GET", "/health") if hasattr(api, "handle") else None
        if response is None or getattr(response, "status_code", None) != 200:
            raise AssertionError("External API health route is not stable")
        return self.report(route_count=len(manifest.get("routes", [])))


def create_external_api_freeze_report(**metadata: Any) -> ExternalApiFreezeReport:
    return ExternalApiFreezeValidator().report(**metadata)

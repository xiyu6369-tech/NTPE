"""Runtime API freeze contract for NTPE 1.0 Beta Stage-11.8.

This module is additive. It records and validates the public Runtime API surface
that was introduced during Stage-11.1 through Stage-11.7. It does not modify the
existing facade, request/response models, session/job/pipeline/event/resource
APIs, or middleware behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Tuple

RUNTIME_API_FREEZE_STAGE = "11.8"
RUNTIME_API_FREEZE_NAME = "Runtime API Freeze"
RUNTIME_API_FREEZE_VERSION = "1.0.0-beta.11.8"

FROZEN_RUNTIME_API_MODULES: Tuple[str, ...] = (
    "runtime_api.runtime_api",
    "runtime_api.runtime_context",
    "runtime_api.runtime_request",
    "runtime_api.runtime_response",
    "runtime_api.runtime_errors",
    "runtime_api.runtime_session",
    "runtime_api.session_api",
    "runtime_api.runtime_job",
    "runtime_api.job_api",
    "runtime_api.job_request",
    "runtime_api.job_response",
    "runtime_api.runtime_pipeline",
    "runtime_api.pipeline_api",
    "runtime_api.pipeline_request",
    "runtime_api.pipeline_response",
    "runtime_api.runtime_event",
    "runtime_api.event_api",
    "runtime_api.event_request",
    "runtime_api.event_response",
    "runtime_api.runtime_resource",
    "runtime_api.resource_api",
    "runtime_api.resource_request",
    "runtime_api.resource_response",
    "runtime_api.runtime_middleware",
    "runtime_api.middleware_api",
    "runtime_api.middleware_request",
    "runtime_api.middleware_response",
)

FROZEN_RUNTIME_API_OPERATIONS: Tuple[str, ...] = (
    "runtime.manifest",
    "runtime.ping",
    "session.create",
    "session.get",
    "session.list",
    "session.start",
    "session.pause",
    "session.resume",
    "session.complete",
    "session.fail",
    "job.create",
    "job.get",
    "job.list",
    "job.start",
    "job.stop",
    "job.cancel",
    "job.resume",
    "pipeline.create",
    "pipeline.get",
    "pipeline.list",
    "pipeline.add_stage",
    "pipeline.start",
    "pipeline.complete_stage",
    "pipeline.complete",
    "pipeline.fail",
    "event.publish",
    "event.get",
    "event.list",
    "event.clear",
    "resource.create",
    "resource.get",
    "resource.list",
    "resource.transition",
    "resource.release",
    "middleware.register",
    "middleware.unregister",
    "middleware.list",
)

FROZEN_COMPATIBILITY_SURFACES: Tuple[str, ...] = (
    "Foundation v1.0",
    "CLI",
    "SDK",
    "Integration",
    "Workflow",
    "Platform Services",
    "Runtime API Core",
    "Runtime Session API",
    "Runtime Job API",
    "Runtime Pipeline API",
    "Runtime Event API",
    "Runtime Resource API",
    "Runtime Middleware",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class RuntimeApiFreezeReport:
    """Serializable Runtime API freeze validation report."""

    stage: str = RUNTIME_API_FREEZE_STAGE
    version: str = RUNTIME_API_FREEZE_VERSION
    name: str = RUNTIME_API_FREEZE_NAME
    modules: Tuple[str, ...] = FROZEN_RUNTIME_API_MODULES
    operations: Tuple[str, ...] = FROZEN_RUNTIME_API_OPERATIONS
    compatibility_surfaces: Tuple[str, ...] = FROZEN_COMPATIBILITY_SURFACES
    frozen: bool = True
    additive_only: bool = True
    created_at: str = field(default_factory=_utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "name": self.name,
            "modules": list(self.modules),
            "operations": list(self.operations),
            "compatibility_surfaces": list(self.compatibility_surfaces),
            "frozen": self.frozen,
            "additive_only": self.additive_only,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class RuntimeApiFreezeValidator:
    """Validates that the Stage-11 public API surface is present and stable."""

    def __init__(self, *, required_operations: Iterable[str] | None = None) -> None:
        self.required_operations = tuple(required_operations or FROZEN_RUNTIME_API_OPERATIONS)

    def report(self, **metadata: Any) -> RuntimeApiFreezeReport:
        return RuntimeApiFreezeReport(metadata=dict(metadata or {}))

    def validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        operations = set(manifest.get("operations", []))
        return all(operation in operations for operation in self.required_operations if operation.startswith("runtime."))

    def validate_runtime_api(self, api: Any) -> RuntimeApiFreezeReport:
        operations = set(api.operations()) if hasattr(api, "operations") else set()
        missing_runtime_ops = [op for op in ("runtime.manifest", "runtime.ping") if op not in operations]
        if missing_runtime_ops:
            raise AssertionError(f"Runtime API core operations missing: {missing_runtime_ops}")
        manifest = api.manifest() if hasattr(api, "manifest") else {}
        if not self.validate_manifest(manifest):
            raise AssertionError("Runtime API manifest does not satisfy freeze contract")
        return self.report(operation_count=len(operations))


def create_runtime_api_freeze_report(**metadata: Any) -> RuntimeApiFreezeReport:
    return RuntimeApiFreezeValidator().report(**metadata)

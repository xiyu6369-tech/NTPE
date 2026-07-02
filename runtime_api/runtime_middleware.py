"""Runtime Middleware model for NTPE 1.0 Beta Stage-11.7.

Middleware is additive: it wraps RuntimeApi execution without modifying existing
request, response, session, job, pipeline, event, or resource APIs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from .runtime_context import utc_now_iso
from .runtime_errors import RuntimeApiValidationError
from .runtime_request import RuntimeApiRequest
from .runtime_response import RuntimeApiResponse

RUNTIME_MIDDLEWARE_VERSION = "1.0.0-beta.11.7"
RUNTIME_MIDDLEWARE_STAGE = "11.7"


class RuntimeMiddlewareState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass(frozen=True)
class RuntimeMiddlewareResult:
    """Result returned by before/after/error middleware hooks."""

    request: Optional[RuntimeApiRequest] = None
    response: Optional[RuntimeApiResponse] = None
    stop: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = RUNTIME_MIDDLEWARE_VERSION
    stage = RUNTIME_MIDDLEWARE_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "stop", bool(self.stop))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True)
class RuntimeMiddleware:
    """Middleware descriptor with ordered hooks."""

    name: str
    priority: int = 100
    state: RuntimeMiddlewareState | str = RuntimeMiddlewareState.ENABLED
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    version = RUNTIME_MIDDLEWARE_VERSION
    stage = RUNTIME_MIDDLEWARE_STAGE

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise RuntimeApiValidationError("middleware name is required")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "priority", int(self.priority))
        object.__setattr__(self, "state", RuntimeMiddlewareState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def enabled(self) -> bool:
        return self.state == RuntimeMiddlewareState.ENABLED

    def before(self, request: RuntimeApiRequest) -> RuntimeMiddlewareResult:
        return RuntimeMiddlewareResult(request=request)

    def after(self, request: RuntimeApiRequest, response: RuntimeApiResponse) -> RuntimeMiddlewareResult:
        return RuntimeMiddlewareResult(request=request, response=response)

    def on_error(self, request: RuntimeApiRequest, error: Exception) -> RuntimeMiddlewareResult:
        return RuntimeMiddlewareResult(request=request, response=RuntimeApiResponse.failure(error, request_id=request.request_id))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "name": self.name,
            "priority": self.priority,
            "state": self.state.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

"""REST authentication hook primitives for NTPE 1.0 Beta Stage-12.7.

This layer is additive. It provides opt-in authentication hooks for future HTTP
servers while keeping the existing REST facade open by default for backward
compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .rest_models import RestRequest, RestResponse

REST_AUTH_API_VERSION = "1.0.0-beta.12.7"
REST_AUTH_API_STAGE = "12.7"


@dataclass(frozen=True)
class RestAuthContext:
    """Immutable authentication context derived from a REST request."""

    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    query: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    @classmethod
    def from_request(cls, request: RestRequest) -> "RestAuthContext":
        return cls(
            method=request.method,
            path=request.path,
            headers=dict(request.headers),
            query=dict(request.query),
            request_id=request.request_id,
        )


@dataclass(frozen=True)
class RestAuthResult:
    """Result returned by an authentication hook."""

    allowed: bool
    principal: Optional[str] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status_code: int = 401

    @classmethod
    def allow(cls, principal: Optional[str] = None, **metadata: Any) -> "RestAuthResult":
        return cls(allowed=True, principal=principal, metadata=dict(metadata))

    @classmethod
    def deny(cls, reason: str, *, status_code: int = 401, **metadata: Any) -> "RestAuthResult":
        return cls(allowed=False, reason=str(reason), status_code=int(status_code), metadata=dict(metadata))


AuthHook = Callable[[RestAuthContext], RestAuthResult]


class RestAuthHooks:
    """Ordered opt-in authentication hook registry.

    No hook is installed by default, so existing tests and users remain fully
    backward compatible. Once a hook is added, every incoming request must pass
    all hooks before the normal REST dispatcher runs.
    """

    version = REST_AUTH_API_VERSION
    stage = REST_AUTH_API_STAGE

    def __init__(self) -> None:
        self._hooks: List[AuthHook] = []

    def add_hook(self, hook: AuthHook) -> "RestAuthHooks":
        if not callable(hook):
            raise ValueError("auth hook must be callable")
        self._hooks.append(hook)
        return self

    def clear(self) -> None:
        self._hooks.clear()

    @property
    def enabled(self) -> bool:
        return bool(self._hooks)

    def require_header(self, header_name: str, expected_value: Optional[str] = None) -> "RestAuthHooks":
        normalized = str(header_name or "").strip().lower()
        if not normalized:
            raise ValueError("header_name is required")

        def _hook(context: RestAuthContext) -> RestAuthResult:
            headers = {str(key).lower(): value for key, value in context.headers.items()}
            actual = headers.get(normalized)
            if actual is None:
                return RestAuthResult.deny("required auth header missing", header=normalized)
            if expected_value is not None and str(actual) != str(expected_value):
                return RestAuthResult.deny("required auth header invalid", header=normalized)
            return RestAuthResult.allow(principal="header-auth", header=normalized)

        return self.add_hook(_hook)

    def evaluate(self, request: RestRequest) -> RestAuthResult:
        context = RestAuthContext.from_request(request)
        principal: Optional[str] = None
        metadata: Dict[str, Any] = {}
        for hook in self._hooks:
            result = hook(context)
            if not isinstance(result, RestAuthResult):
                raise ValueError("auth hook must return RestAuthResult")
            if not result.allowed:
                return result
            principal = result.principal or principal
            metadata.update(result.metadata)
        return RestAuthResult.allow(principal=principal, **metadata)

    def response_for_denial(self, result: RestAuthResult, request: RestRequest) -> RestResponse:
        return RestResponse.error(
            result.status_code,
            result.reason or "request unauthorized",
            request_id=request.request_id,
            details={"principal": result.principal, "metadata": dict(result.metadata)},
        )

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "enabled": self.enabled,
            "hook_count": len(self._hooks),
            "default_policy": "allow_when_no_hooks",
            "additive_only": True,
        }

"""REST middleware chain for NTPE 1.0 Beta Stage-12.7.

Middleware is additive and opt-in. It can observe or short-circuit REST requests
without changing the frozen Runtime API contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .rest_models import RestRequest, RestResponse

REST_MIDDLEWARE_API_VERSION = "1.0.0-beta.12.7"
REST_MIDDLEWARE_API_STAGE = "12.7"


@dataclass
class RestMiddlewareContext:
    """Mutable per-request middleware context."""

    request: RestRequest
    metadata: Dict[str, Any] = field(default_factory=dict)


BeforeMiddleware = Callable[[RestMiddlewareContext], Optional[RestResponse]]
AfterMiddleware = Callable[[RestMiddlewareContext, RestResponse], RestResponse]


class RestMiddlewareChain:
    """Ordered before/after middleware chain."""

    version = REST_MIDDLEWARE_API_VERSION
    stage = REST_MIDDLEWARE_API_STAGE

    def __init__(self) -> None:
        self._before: List[BeforeMiddleware] = []
        self._after: List[AfterMiddleware] = []

    def add_before(self, middleware: BeforeMiddleware) -> "RestMiddlewareChain":
        if not callable(middleware):
            raise ValueError("before middleware must be callable")
        self._before.append(middleware)
        return self

    def add_after(self, middleware: AfterMiddleware) -> "RestMiddlewareChain":
        if not callable(middleware):
            raise ValueError("after middleware must be callable")
        self._after.append(middleware)
        return self

    def clear(self) -> None:
        self._before.clear()
        self._after.clear()

    @property
    def enabled(self) -> bool:
        return bool(self._before or self._after)

    def before_count(self) -> int:
        return len(self._before)

    def after_count(self) -> int:
        return len(self._after)

    def run_before(self, context: RestMiddlewareContext) -> Optional[RestResponse]:
        for middleware in self._before:
            response = middleware(context)
            if response is not None:
                if not isinstance(response, RestResponse):
                    raise ValueError("before middleware must return RestResponse or None")
                return response
        return None

    def run_after(self, context: RestMiddlewareContext, response: RestResponse) -> RestResponse:
        current = response
        for middleware in self._after:
            current = middleware(context, current)
            if not isinstance(current, RestResponse):
                raise ValueError("after middleware must return RestResponse")
        return current

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "enabled": self.enabled,
            "before_count": self.before_count(),
            "after_count": self.after_count(),
            "additive_only": True,
            "uses_frozen_runtime_api_only": True,
        }

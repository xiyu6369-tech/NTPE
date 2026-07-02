"""Additive REST router for NTPE Stage-12.1."""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .rest_models import RestRequest, RestResponse

RestHandler = Callable[[RestRequest], RestResponse]


class RestRouter:
    """Minimal deterministic router used before introducing an HTTP server."""

    def __init__(self) -> None:
        self._routes: Dict[Tuple[str, str], RestHandler] = {}

    def add_route(self, method: str, path: str, handler: RestHandler) -> "RestRouter":
        if not callable(handler):
            raise ValueError("REST route handler must be callable")
        request = RestRequest(method=method, path=path)
        self._routes[(request.method, request.path)] = handler
        return self

    def routes(self) -> tuple[Tuple[str, str], ...]:
        return tuple(sorted(self._routes.keys()))

    def dispatch(self, request: RestRequest) -> RestResponse:
        handler = self._routes.get((request.method, request.path))
        if handler is None:
            return RestResponse.error(
                404,
                "REST route not found",
                request_id=request.request_id,
                details={"method": request.method, "path": request.path},
            )
        try:
            return handler(request)
        except Exception as exc:  # noqa: BLE001 - external facade normalizes failures
            return RestResponse.error(500, "REST route execution failed", request_id=request.request_id, details={"cause": repr(exc)})

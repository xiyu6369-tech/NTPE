"""Runtime Middleware API for NTPE 1.0 Beta Stage-11.7.

Registers middleware.* operations and offers a wrapped execute path. Existing
RuntimeApi.execute remains available and unchanged; consumers opt in by using
RuntimeMiddlewareApi.execute or middleware.execute.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .middleware_request import RuntimeMiddlewareRegisterRequest
from .middleware_response import RuntimeMiddlewareListResponse
from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_middleware import RuntimeMiddleware, RuntimeMiddlewareResult, RuntimeMiddlewareState
from .runtime_request import RuntimeApiRequest
from .runtime_response import RuntimeApiResponse


class RuntimeMiddlewareApi:
    """Additive middleware facade for Runtime API consumers."""

    operations = (
        "middleware.register",
        "middleware.get",
        "middleware.list",
        "middleware.enable",
        "middleware.disable",
        "middleware.remove",
        "middleware.summary",
        "middleware.execute",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._middlewares: Dict[str, RuntimeMiddleware] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        for operation in self.operations:
            self.runtime_api.register(operation, getattr(self, f"_handle_{operation.split('.')[1]}"))

    def register(self, middleware: RuntimeMiddleware | None = None, **kwargs: Any) -> RuntimeMiddleware:
        registered = middleware or RuntimeMiddleware(**RuntimeMiddlewareRegisterRequest(**kwargs).to_payload())
        self._middlewares[registered.name] = registered
        return registered

    def get(self, name: str) -> RuntimeMiddleware:
        middleware = self._middlewares.get(str(name))
        if middleware is None:
            raise RuntimeApiNotFoundError("runtime middleware not found", details={"name": str(name)})
        return middleware

    def list(self) -> tuple[RuntimeMiddleware, ...]:
        return tuple(sorted(self._middlewares.values(), key=lambda item: (item.priority, item.name)))

    def enabled(self) -> tuple[RuntimeMiddleware, ...]:
        return tuple(middleware for middleware in self.list() if middleware.enabled)

    def set_state(self, name: str, state: RuntimeMiddlewareState | str) -> RuntimeMiddleware:
        current = self.get(name)
        updated = RuntimeMiddleware(name=current.name, priority=current.priority, state=state, metadata=current.metadata, created_at=current.created_at)
        self._middlewares[updated.name] = updated
        return updated

    def remove(self, name: str) -> bool:
        return self._middlewares.pop(str(name), None) is not None

    def summary(self) -> Dict[str, Any]:
        all_middlewares = self.list()
        return {
            "count": len(all_middlewares),
            "enabled": len([middleware for middleware in all_middlewares if middleware.enabled]),
            "disabled": len([middleware for middleware in all_middlewares if not middleware.enabled]),
            "names": [middleware.name for middleware in all_middlewares],
            "operations": list(self.operations),
        }

    def execute(self, request: RuntimeApiRequest | str, payload: Optional[Dict[str, Any]] = None, *, metadata: Optional[Dict[str, Any]] = None) -> RuntimeApiResponse:
        api_request = request if isinstance(request, RuntimeApiRequest) else self.runtime_api.request(str(request), payload, metadata=metadata)
        active_middlewares = self.enabled()
        try:
            for middleware in active_middlewares:
                before_result = middleware.before(api_request)
                api_request = before_result.request or api_request
                if before_result.stop:
                    return before_result.response or RuntimeApiResponse.success(None, request_id=api_request.request_id, metadata={"stopped_by": middleware.name})

            response = self.runtime_api.execute(api_request)

            for middleware in reversed(active_middlewares):
                after_result = middleware.after(api_request, response)
                response = after_result.response or response
                if after_result.stop:
                    break
            return response
        except Exception as exc:  # noqa: BLE001 - middleware layer normalizes hook failures
            response = RuntimeApiResponse.failure(exc, request_id=api_request.request_id)
            for middleware in reversed(active_middlewares):
                error_result = middleware.on_error(api_request, exc)
                response = error_result.response or response
                if error_result.stop:
                    break
            return response

    def _middleware_name_from(self, request: RuntimeApiRequest) -> str:
        name = request.payload.get("name")
        if not name:
            raise RuntimeApiValidationError("middleware name is required", details={"operation": request.operation})
        return str(name)

    def _handle_register(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.register(RuntimeMiddleware(**RuntimeMiddlewareRegisterRequest.from_payload(request.payload).to_payload())).to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._middleware_name_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return RuntimeMiddlewareListResponse.from_middlewares(self.list()).to_dict()

    def _handle_enable(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.set_state(self._middleware_name_from(request), RuntimeMiddlewareState.ENABLED).to_dict()

    def _handle_disable(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.set_state(self._middleware_name_from(request), RuntimeMiddlewareState.DISABLED).to_dict()

    def _handle_remove(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return {"removed": self.remove(self._middleware_name_from(request))}

    def _handle_summary(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.summary()

    def _handle_execute(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        operation = request.payload.get("operation")
        if not operation:
            raise RuntimeApiValidationError("middleware execute operation is required")
        response = self.execute(str(operation), request.payload.get("payload") or {}, metadata=request.payload.get("metadata") or {})
        return response.to_dict()


def attach_middleware_api(runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> RuntimeMiddlewareApi:
    return RuntimeMiddlewareApi(runtime_api=runtime_api, context=context)

"""Focused assertions for Runtime Middleware API."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime_api import RuntimeApi, RuntimeMiddleware, RuntimeMiddlewareApi, RuntimeMiddlewareResult, RuntimeApiResponse


class RewriteMiddleware(RuntimeMiddleware):
    def before(self, request):
        rewritten = type(request)(operation="runtime.ping", payload=request.payload, request_id=request.request_id, metadata=request.metadata)
        return RuntimeMiddlewareResult(request=rewritten)


class TagMiddleware(RuntimeMiddleware):
    def after(self, request, response):
        return RuntimeMiddlewareResult(
            request=request,
            response=RuntimeApiResponse.success({"tagged": True, "source_ok": response.ok}, request_id=request.request_id),
        )


def test_middleware_order_and_hooks():
    api = RuntimeApi()
    middleware = RuntimeMiddlewareApi(runtime_api=api)
    middleware.register(TagMiddleware(name="tag", priority=20))
    middleware.register(RewriteMiddleware(name="rewrite", priority=10))
    response = middleware.execute("missing.operation")
    assert response.ok is True
    assert response.data["tagged"] is True
    assert response.data["source_ok"] is True
    assert middleware.summary()["count"] == 2


if __name__ == "__main__":
    test_middleware_order_and_hooks()
    print("PASS")

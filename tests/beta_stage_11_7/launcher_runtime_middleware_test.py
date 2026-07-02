"""Launcher test for NTPE Stage-11.7 Runtime Middleware."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime_api import RuntimeApi, RuntimeMiddleware, RuntimeMiddlewareApi, RuntimeMiddlewareResult, RuntimeApiResponse


class AddMetadataMiddleware(RuntimeMiddleware):
    def after(self, request, response):
        data = response.to_dict()
        data["metadata"]["middleware"] = self.name
        return RuntimeMiddlewareResult(request=request, response=RuntimeApiResponse.success(data, request_id=request.request_id))


class StopMiddleware(RuntimeMiddleware):
    def before(self, request):
        return RuntimeMiddlewareResult(
            request=request,
            response=RuntimeApiResponse.success({"stopped": True, "operation": request.operation}, request_id=request.request_id),
            stop=True,
        )


def check(label, condition):
    print(f"{label:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    print("NTPE Stage-11.7 Runtime Middleware Test")
    print("=" * 52)
    api = RuntimeApi()
    middleware = RuntimeMiddlewareApi(runtime_api=api)

    check("Middleware API Created", middleware is not None)
    check("Operation Registered", "middleware.register" in api.operations())

    registered = middleware.register(name="audit", priority=10, metadata={"scope": "runtime"})
    check("Middleware Registered", registered.name == "audit")
    check("Middleware Retrieved", middleware.get("audit").priority == 10)
    check("Middleware Listed", len(middleware.list()) == 1)
    check("Middleware Summary", middleware.summary()["enabled"] == 1)

    disabled = middleware.set_state("audit", "disabled")
    check("Middleware Disabled", disabled.state.value == "disabled")
    enabled = middleware.set_state("audit", "enabled")
    check("Middleware Enabled", enabled.state.value == "enabled")

    middleware.register(AddMetadataMiddleware(name="metadata", priority=20))
    response = middleware.execute("runtime.ping")
    check("Middleware Execute", response.ok is True)
    check("Middleware After Hook", response.data["metadata"]["middleware"] == "metadata")

    middleware.register(StopMiddleware(name="stopper", priority=1))
    stopped = middleware.execute("runtime.ping")
    check("Middleware Stop", stopped.ok is True and stopped.data["stopped"] is True)

    facade = api.execute("middleware.summary")
    check("Facade Summary", facade.ok is True and facade.data["count"] >= 3)
    check("Backward Compatible", "runtime.ping" in api.operations())
    print("PASS")


if __name__ == "__main__":
    main()

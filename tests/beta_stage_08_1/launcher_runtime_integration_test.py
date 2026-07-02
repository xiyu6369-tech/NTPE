"""NTPE 1.0 Beta Stage-08.1 Runtime Integration test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    IntegrationCore,
    RuntimeBridge,
    RuntimeCommand,
    RuntimeContext,
    RuntimeDispatcher,
    RuntimeEventBridge,
    RuntimeManager,
    RuntimeRegistry,
    RUNTIME_INTEGRATION_STAGE,
    RUNTIME_INTEGRATION_VERSION,
)
from sdk import NTPEClient, SDKPluginManager  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-stub-08.1"

    def __init__(self) -> None:
        self.started = False
        self.executed = []

    def start(self, **payload):
        self.started = True
        return {"status": "started", "payload": payload}

    def execute(self, text="", **payload):
        self.executed.append({"text": text, **payload})
        return {"translation": text, "count": len(self.executed)}

    def resume(self, **payload):
        return {"status": "resumed", "payload": payload}

    def stop(self, **payload):
        self.started = False
        return {"status": "stopped", "payload": payload}

    def status(self):
        return {"status": "ready" if self.started else "idle", "executions": len(self.executed)}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.1 Runtime Integration Test")
    print("=" * 72)

    check("Runtime Integration Stage", "Stage-08.1" in RUNTIME_INTEGRATION_STAGE and RUNTIME_INTEGRATION_VERSION == "0.8.1")

    events = RuntimeEventBridge()
    seen = []
    events.subscribe(lambda event: seen.append(event.to_dict()))
    bridge = RuntimeBridge(events=events)
    runtime_id = bridge.attach(RuntimeStub(), name="runtime-stub", metadata={"stage": "08.1"})
    check("Runtime Bridge", runtime_id.startswith("rt-") and events.events[-1].event_type == "runtime.created")

    registry = bridge.registry
    check("Runtime Registry", registry.require(runtime_id) is not None and registry.manifest()["count"] == 1)

    dispatcher = RuntimeDispatcher(registry)
    dispatched = dispatcher.dispatch(RuntimeCommand("execute", runtime_id=runtime_id, payload={"text": "dispatch-ok"}))
    check("Runtime Dispatcher", dispatched.ok and dispatched.value["translation"] == "dispatch-ok")

    context = RuntimeContext(operation="runtime.translate", runtime_id=runtime_id, job_id="job-081")
    child = context.child("runtime.segment", index=1)
    check("Runtime Context", child.runtime_id == runtime_id and child.metadata["parent_correlation_id"] == context.correlation_id)

    manager = RuntimeManager(bridge=bridge)
    start = manager.start(runtime_id, source="test")
    run = manager.execute(runtime_id, text="runtime-ok")
    resume = manager.resume(runtime_id, checkpoint="ckpt-1")
    status = manager.status(runtime_id)
    stop = manager.shutdown(runtime_id)
    check("Runtime Manager", start.ok and run.ok and resume.ok and stop.ok and status["metadata"]["runtime_id"] == runtime_id)

    core = IntegrationCore(metadata={"stage": "08.1"})
    core.bridge_runtime(manager, name="runtime_manager")
    core.bridge_sdk(NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}))
    core.bridge_plugin_manager(SDKPluginManager())
    invoked = core.invoke("runtime_manager", "status", runtime_id)
    check("CLI Integration", invoked.ok and "metadata" in invoked.data["value"])
    check("SDK Integration", core.invoke("sdk", "translate_text", "sdk-ok").data["value"].text == "sdk-ok")
    check("Plugin Integration", "plugin_manager" in core.registry.names())

    manifest = manager.manifest()
    check("Runtime Events", manifest["events"]["count"] >= 5 and len(seen) >= 5)
    check("Foundation Freeze", core.manifest()["foundation_status"] == "frozen")
    check("Backward Compatible", NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}).translate_text("compat").ok)

    print("PASS")


if __name__ == "__main__":
    main()

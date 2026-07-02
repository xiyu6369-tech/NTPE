"""NTPE 1.0 Beta Stage-10.6 Service Lifecycle Hooks test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_LIFECYCLE_STAGE,
    PlatformEventBus,
    PlatformLifecycleExecution,
    PlatformLifecycleHooks,
    PlatformLifecyclePhase,
    PlatformServiceLifecycle,
    create_event_bus,
    create_lifecycle_hooks,
    create_service_lifecycle,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class DemoService:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True
        return {"started": True}

    def stop(self):
        self.stopped = True
        return {"stopped": True}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.6 Service Lifecycle Hooks Test")
    print("=" * 82)

    calls = []
    bus = create_event_bus(metadata={"stage": "10.6"})
    hooks = create_lifecycle_hooks(event_bus=bus, metadata={"stage": "10.6"})
    check("Lifecycle Stage", PLATFORM_LIFECYCLE_STAGE == "10.6")
    check("Lifecycle Hooks Type", isinstance(hooks, PlatformLifecycleHooks))
    check("Event Bus Type", isinstance(bus, PlatformEventBus))

    before = hooks.register(PlatformLifecyclePhase.BEFORE_START, lambda ctx: calls.append(("before", ctx.service_name)), priority=10)
    after = hooks.register("after_start", lambda ctx: calls.append(("after", ctx.service_name)), service_name="translator", priority=20)
    check("Hooks Registered", before.active and after.active and len(hooks.hooks(active_only=True)) == 2)

    executions = hooks.execute("before_start", "translator", action="start")
    check("Before Hook Executed", len(executions) == 1 and executions[0].ok and calls == [("before", "translator")])
    check("Execution Type", isinstance(executions[0], PlatformLifecycleExecution))

    lifecycle = create_service_lifecycle(hooks, metadata={"adapter": "test"})
    service = DemoService()
    value = lifecycle.start_service("translator", service)
    check("Service Lifecycle Type", isinstance(lifecycle, PlatformServiceLifecycle))
    check("Service Started", service.started and value["started"] is True)
    check("After Hook Executed", ("after", "translator") in calls)

    lifecycle.stop_service("translator", service)
    check("Service Stopped", service.stopped is True)

    bad_hook = hooks.register("before_stop", lambda ctx: (_ for _ in ()).throw(RuntimeError("hook failure")), service_name="translator")
    failure_executions = hooks.execute("before_stop", "translator")
    check("Hook Failure Captured", any(not item.ok and item.error == "hook failure" for item in failure_executions))

    removed = hooks.unregister(bad_hook.hook_id)
    check("Hook Unregistered", removed and not bad_hook.active)

    summary = hooks.summary()
    check("Lifecycle Summary", summary["hook_count"] == 3 and summary["failed_execution_count"] >= 1)
    check("Event Bridge", len(bus.history(event_type="platform.lifecycle.hook.executed")) >= 4)

    manifest = hooks.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)
    print("PASS")


if __name__ == "__main__":
    main()

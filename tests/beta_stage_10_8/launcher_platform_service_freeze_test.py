"""NTPE 1.0 Beta Stage-10.8 Platform Service Freeze test."""
from __future__ import annotations

import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_FREEZE_VERSION,
    PLATFORM_FREEZE_STATUS,
    PLATFORM_FREEZE_STAGE,
    PLATFORM_FROZEN_SURFACES,
    PlatformServiceManager,
    create_platform_config,
    create_service_discovery,
    create_health_monitor,
    create_metrics_registry,
    create_event_bus,
    create_lifecycle_hooks,
    create_policy_engine,
    build_platform_freeze_manifest,
    build_platform_service_contract,
    build_platform_compatibility_matrix,
    build_platform_version_manifest,
    validate_platform_freeze_manifest,
    platform_freeze_is_compatible,
    write_platform_freeze_artifacts,
    load_platform_json,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<38} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class DemoService:
    def __init__(self) -> None:
        self.started = False

    def start(self):
        self.started = True
        return {"started": True}

    def stop(self):
        self.started = False
        return {"stopped": True}

    def health_check(self):
        return {"ok": True, "message": "demo healthy"}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.8 Platform Service Freeze Test")
    print("=" * 86)

    manifest = build_platform_freeze_manifest({"stage": "10.8"})
    result = validate_platform_freeze_manifest(manifest)
    contract = build_platform_service_contract()
    matrix = build_platform_compatibility_matrix()
    version = build_platform_version_manifest()

    check("Freeze Version", PLATFORM_FREEZE_VERSION == "1.0.0-beta.10.8")
    check("Freeze Stage", PLATFORM_FREEZE_STAGE == "10.8")
    check("Platform Freeze", result.ok and result.status == PLATFORM_FREEZE_STATUS)
    check("Platform Contract", contract["status"] == "frozen" and len(contract["frozen_surfaces"]) >= 18)
    check("Compatibility Matrix", platform_freeze_is_compatible(matrix))
    check("Version Manifest", version["version"] == PLATFORM_FREEZE_VERSION and version["status"] == "frozen")

    bus = create_event_bus(metadata={"stage": "10.8"})
    metrics = create_metrics_registry(metadata={"stage": "10.8"})
    config = create_platform_config(metadata={"stage": "10.8"})
    manager = PlatformServiceManager(event_bus=bus, metadata={"stage": "10.8"})

    descriptor = manager.register_service("demo", DemoService(), metadata={"component": "freeze"})
    start_result = manager.start_service("demo")
    discovery = create_service_discovery(manager.registry, metadata={"stage": "10.8"})
    health = create_health_monitor(manager.registry, metadata={"stage": "10.8"})
    hooks = create_lifecycle_hooks(event_bus=bus, metadata={"stage": "10.8"})
    policy = create_policy_engine(event_bus=bus, metrics=metrics, metadata={"stage": "10.8"})

    config.set("platform.freeze.status", "frozen")
    discovered = discovery.by_name("demo")
    snapshot = health.check_all()
    hooks.register("custom", lambda ctx: {"hook": ctx.phase.value})
    hook_executions = hooks.execute("custom", service_name="demo")
    policy.allow("allow-start", lambda ctx: ctx.action == "start", priority=1)
    policy_result = policy.evaluate({"service_name": "demo", "action": "start"})
    manager_health = manager.health()
    stop_result = manager.stop_service("demo")

    check("Service Manager Compatible", descriptor.name == "demo" and start_result.ok and stop_result.ok)
    check("Config Compatible", config.get("platform.freeze.status") == "frozen")
    check("Discovery Compatible", discovered is not None and discovered.name == "demo")
    check("Health Compatible", snapshot.summary()["count"] >= 1)
    metrics.counter("platform.freeze.checks")
    check("Metrics Compatible", metrics.get("platform.freeze.checks") is not None)
    check("Event Bus Compatible", len(bus.history()) >= 3)
    check("Lifecycle Compatible", len(hook_executions) == 1 and hook_executions[0].ok)
    check("Policy Compatible", policy_result.allowed is True)
    check("Manager Health Compatible", manager_health["ok"] is True and manager.manifest()["workflow_status"] == "frozen")

    check("Frozen Surface Count", len(PLATFORM_FROZEN_SURFACES) >= 18)
    check("Foundation Freeze", manifest["foundation_status"] == "frozen")
    check("CLI Freeze", manifest["cli_status"] == "frozen")
    check("SDK Complete", manifest["sdk_status"] == "complete")
    check("Integration Freeze", manifest["integration_status"] == "frozen")
    check("Workflow Freeze", manifest["workflow_status"] == "frozen")
    check("Platform Freeze Status", manifest["platform_services_status"] == "frozen")
    check("Backward Compatible", manifest["additive_only"] is True and contract["rules"]["backward_compatible"] is True)

    with tempfile.TemporaryDirectory() as tmp:
        written = write_platform_freeze_artifacts(tmp, {"stage": "10.8"})
        loaded_manifest = load_platform_json(written["platform_freeze_manifest.json"])
        loaded_matrix = load_platform_json(written["platform_compatibility_matrix.json"])
        check("Freeze Artifacts", len(written) == 4 and validate_platform_freeze_manifest(loaded_manifest).ok)
        check("Artifact Compatibility", platform_freeze_is_compatible(loaded_matrix))

    print("PASS")


if __name__ == "__main__":
    main()

"""NTPE 1.0 Beta Stage-10.3 Service Health Monitor test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_HEALTH_STAGE,
    PlatformHealthCheckResult,
    PlatformHealthLevel,
    PlatformServiceHealthMonitor,
    PlatformServiceStatus,
    create_health_monitor,
    create_platform_service_host,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class HealthyService:
    def start(self):
        return {"started": True}

    def health(self):
        return {"level": "healthy", "ok": True, "message": "ready", "metadata": {"kind": "demo"}}


class WarningService:
    def health_check(self):
        return PlatformHealthCheckResult.warning("warning_service", "degraded dependency")


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.3 Service Health Monitor Test")
    print("=" * 78)

    host = create_platform_service_host(metadata={"stage": "10.3"})
    healthy = host.register_service("healthy_service", HealthyService(), metadata={"tags": ["health"]})
    warning = host.register_service("warning_service", WarningService(), metadata={"tags": ["health"]})
    failed = host.register_service("failed_service", object(), metadata={"tags": ["health"]})
    failed.status = PlatformServiceStatus.FAILED

    monitor = create_health_monitor(host.manager.registry, metadata={"stage": "10.3"})
    check("Health Stage", PLATFORM_HEALTH_STAGE == "10.3")
    check("Monitor Type", isinstance(monitor, PlatformServiceHealthMonitor))

    monitor.register_check("healthy_service", lambda descriptor: True)
    healthy_result = monitor.check_service("healthy_service")
    check("Health Check PASS", healthy_result.ok is True and healthy_result.level == PlatformHealthLevel.HEALTHY)

    warning_result = monitor.check_service("warning_service")
    check("Warning Check", warning_result.level == PlatformHealthLevel.WARNING)

    failed_result = monitor.check_service("failed_service")
    check("Critical Check", failed_result.level == PlatformHealthLevel.CRITICAL)

    missing_result = monitor.check_service("missing_service")
    check("Unknown Check", missing_result.level == PlatformHealthLevel.UNKNOWN)

    snapshot = monitor.check_all(["healthy_service", "warning_service", "failed_service"])
    check("Health Snapshot", snapshot.count == 3 and snapshot.overall_level == PlatformHealthLevel.CRITICAL)

    summary = snapshot.summary()
    check("Health Summary", summary["healthy"] == 1 and summary["warning"] == 1 and summary["critical"] == 1)

    report = snapshot.report()
    check("Health Report", report["stage"] == "10.3" and report["services"]["healthy_service"]["ok"] is True)
    check("Response Time", report["services"]["healthy_service"]["response_time_ms"] >= 0)

    manifest = monitor.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)

    # Existing host health remains backward compatible.
    legacy_health = host.health()
    check("Legacy Health Compatible", legacy_health["count"] == 3 and "healthy_service" in legacy_health["services"])

    check("Descriptor Preserved", healthy.name == "healthy_service" and warning.name == "warning_service")
    print("PASS")


if __name__ == "__main__":
    main()

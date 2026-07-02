"""NTPE 1.0 Beta Stage-10.4 Metrics & Telemetry test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_METRICS_STAGE,
    PLATFORM_TELEMETRY_STAGE,
    PlatformMetricsRegistry,
    PlatformTelemetryBuffer,
    PlatformTelemetryEvent,
    create_health_monitor,
    create_metrics_registry,
    create_platform_service_host,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class HealthyService:
    def health(self):
        return {"level": "healthy", "ok": True, "message": "ready"}


class WarningService:
    def health(self):
        return {"level": "warning", "ok": False, "message": "degraded"}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.4 Metrics & Telemetry Test")
    print("=" * 78)

    telemetry = PlatformTelemetryBuffer(max_events=20)
    metrics = create_metrics_registry(telemetry=telemetry, metadata={"stage": "10.4"})

    check("Metrics Stage", PLATFORM_METRICS_STAGE == "10.4")
    check("Telemetry Stage", PLATFORM_TELEMETRY_STAGE == "10.4")
    check("Metrics Type", isinstance(metrics, PlatformMetricsRegistry))

    c1 = metrics.counter("service.requests")
    c2 = metrics.counter("service.requests", 2)
    check("Counter Update", c1.value == 1.0 and c2.value == 3.0)

    gauge = metrics.gauge("service.queue.depth", 7, unit="items")
    check("Gauge Update", gauge.value == 7.0 and gauge.unit == "items")

    timer = metrics.timer("service.latency", 12.5)
    check("Timer Update", timer.value == 12.5 and timer.unit == "ms")

    with metrics.time_block("service.block"):
        sum(range(10))
    check("Timer Context", metrics.get("service.block") is not None)

    event = telemetry.record("service.custom", source="test", message="custom event", metadata={"ok": True})
    check("Telemetry Event", isinstance(event, PlatformTelemetryEvent) and event.event_type == "service.custom")

    snapshot = metrics.snapshot()
    check("Metrics Snapshot", snapshot.count >= 4 and snapshot.stage == "10.4")

    summary = snapshot.summary()
    check("Metrics Summary", summary["by_type"]["counter"] == 1 and summary["by_type"]["gauge"] == 1)

    host = create_platform_service_host(metadata={"stage": "10.4"})
    host.register_service("healthy_service", HealthyService())
    host.register_service("warning_service", WarningService())
    health = create_health_monitor(host.manager.registry).check_all()
    metrics.record_health_snapshot(health)
    check("Health Integration", metrics.get("platform.health.healthy").value == 1.0 and metrics.get("platform.health.warning").value == 1.0)

    report = metrics.report()
    check("Metrics Report", report["stage"] == "10.4" and report["telemetry"]["count"] >= 1)

    manifest = metrics.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)

    legacy_health = host.health()
    check("Legacy Health Compatible", legacy_health["count"] == 2 and "healthy_service" in legacy_health["services"])
    print("PASS")


if __name__ == "__main__":
    main()

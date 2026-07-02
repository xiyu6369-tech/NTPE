"""Platform metrics registry for NTPE 1.0 Beta Stage-10.4.

Metrics are additive and optional. They do not mutate frozen Foundation, CLI,
SDK, Integration, or Workflow behavior.
"""
from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Any, Dict, Iterator, Optional

from .metrics_snapshot import (
    PLATFORM_METRICS_STAGE,
    PLATFORM_METRICS_VERSION,
    PlatformMetricPoint,
    PlatformMetricsSnapshot,
)
from .telemetry import PlatformTelemetryBuffer


class PlatformMetricsRegistry:
    """In-memory counter/gauge/timer metrics registry."""

    version = PLATFORM_METRICS_VERSION
    stage = PLATFORM_METRICS_STAGE

    def __init__(self, *, telemetry: Optional[PlatformTelemetryBuffer] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.telemetry = telemetry or PlatformTelemetryBuffer()
        self.metadata = dict(metadata or {})
        self._metrics: Dict[str, PlatformMetricPoint] = {}

    def counter(self, name: str, value: float = 1.0, *, unit: str = "count", metadata: Optional[Dict[str, Any]] = None) -> PlatformMetricPoint:
        current = self._metrics.get(str(name))
        base = current.value if current and current.metric_type == "counter" else 0.0
        point = PlatformMetricPoint(str(name), base + float(value), "counter", unit=unit, metadata=dict(metadata or {}))
        self._metrics[point.name] = point
        self.telemetry.record("metric.counter", source="platform.metrics", message=point.name, metadata=point.to_dict())
        return point

    def gauge(self, name: str, value: float, *, unit: str = "value", metadata: Optional[Dict[str, Any]] = None) -> PlatformMetricPoint:
        point = PlatformMetricPoint(str(name), float(value), "gauge", unit=unit, metadata=dict(metadata or {}))
        self._metrics[point.name] = point
        self.telemetry.record("metric.gauge", source="platform.metrics", message=point.name, metadata=point.to_dict())
        return point

    def timer(self, name: str, value_ms: float, *, metadata: Optional[Dict[str, Any]] = None) -> PlatformMetricPoint:
        point = PlatformMetricPoint(str(name), float(value_ms), "timer", unit="ms", metadata=dict(metadata or {}))
        self._metrics[point.name] = point
        self.telemetry.record("metric.timer", source="platform.metrics", message=point.name, metadata=point.to_dict())
        return point

    @contextmanager
    def time_block(self, name: str, *, metadata: Optional[Dict[str, Any]] = None) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            elapsed = (perf_counter() - started_at) * 1000.0
            self.timer(name, round(elapsed, 3), metadata=metadata)

    def get(self, name: str) -> Optional[PlatformMetricPoint]:
        return self._metrics.get(str(name))

    def snapshot(self) -> PlatformMetricsSnapshot:
        return PlatformMetricsSnapshot(dict(self._metrics), metadata={"source": "metrics_registry", **self.metadata})

    def summary(self) -> Dict[str, Any]:
        return self.snapshot().summary()

    def report(self) -> Dict[str, Any]:
        payload = self.snapshot().report()
        payload["telemetry"] = self.telemetry.summary()
        return payload

    def record_health_snapshot(self, health_snapshot: Any) -> "PlatformMetricsRegistry":
        """Bridge Stage-10.3 health snapshots into Stage-10.4 metrics."""
        summary = health_snapshot.summary() if hasattr(health_snapshot, "summary") else dict(health_snapshot)
        prefix = "platform.health"
        for key in ("count", "healthy", "warning", "critical", "unknown"):
            self.gauge(f"{prefix}.{key}", float(summary.get(key, 0)), unit="services", metadata={"source": "health_snapshot"})
        self.telemetry.record("health.snapshot", source="platform.health", message=str(summary.get("overall_level", "unknown")), metadata=summary)
        return self

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "metric_count": len(self._metrics),
            "telemetry_count": self.telemetry.summary()["count"],
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
            "metadata": dict(self.metadata),
        }


def create_metrics_registry(**kwargs: Any) -> PlatformMetricsRegistry:
    return PlatformMetricsRegistry(**kwargs)

"""Platform metrics snapshot models for NTPE 1.0 Beta Stage-10.4.

This module is additive and keeps Foundation, CLI, SDK, Integration, and
Workflow frozen contracts unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

PLATFORM_METRICS_VERSION = "1.0.0-beta.10.4"
PLATFORM_METRICS_STAGE = "10.4"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class PlatformMetricPoint:
    """Single normalized metric value."""

    name: str
    value: float
    metric_type: str
    unit: str = "count"
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ValueError("metric name is required")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "metric_type", str(self.metric_type))
        object.__setattr__(self, "unit", str(self.unit))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "metric_type": self.metric_type,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlatformMetricsSnapshot:
    """Immutable snapshot of current platform metrics."""

    metrics: Mapping[str, PlatformMetricPoint]
    generated_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = PLATFORM_METRICS_VERSION
    stage = PLATFORM_METRICS_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def count(self) -> int:
        return len(self.metrics)

    def summary(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for metric in self.metrics.values():
            by_type[metric.metric_type] = by_type.get(metric.metric_type, 0) + 1
        return {
            "version": self.version,
            "stage": self.stage,
            "count": self.count,
            "by_type": by_type,
            "generated_at": self.generated_at,
        }

    def report(self) -> Dict[str, Any]:
        payload = self.summary()
        payload.update({
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "metadata": dict(self.metadata),
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
        })
        return payload

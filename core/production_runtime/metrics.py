"""NTPE 1.0 Beta Stage-01 Production Runtime metrics."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict


class RuntimeMetrics:
    """Small metrics collector for production runtime observability."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self):
        self.started_at = time.time()
        self.counters = defaultdict(int)
        self.timings = defaultdict(list)
        self.gauges: Dict[str, Any] = {}

    def increment(self, name: str, value: int = 1) -> int:
        self.counters[str(name)] += int(value)
        return self.counters[str(name)]

    def observe(self, name: str, duration: float) -> float:
        self.timings[str(name)].append(float(duration))
        return float(duration)

    def gauge(self, name: str, value: Any) -> Any:
        self.gauges[str(name)] = value
        return value

    def snapshot(self) -> Dict[str, Any]:
        timing_summary = {}
        for name, values in self.timings.items():
            if not values:
                continue
            timing_summary[name] = {
                "count": len(values),
                "total": sum(values),
                "avg": sum(values) / len(values),
                "max": max(values),
                "min": min(values),
            }
        return {
            "version": self.version,
            "uptime_seconds": time.time() - self.started_at,
            "counters": dict(self.counters),
            "timings": timing_summary,
            "gauges": dict(self.gauges),
        }

    def manifest(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "name": "production_runtime_metrics",
            "version": self.version,
            "counters": snap["counters"],
            "timing_names": list(snap["timings"].keys()),
        }


__all__ = ["RuntimeMetrics"]

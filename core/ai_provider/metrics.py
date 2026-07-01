from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ProviderMetrics:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    by_provider: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    def record(self, provider: str, success: bool, latency_ms: float = 0.0):
        self.calls += 1
        self.successes += 1 if success else 0
        self.failures += 0 if success else 1
        self.total_latency_ms += latency_ms
        row = self.by_provider.setdefault(provider, {"calls": 0, "successes": 0, "failures": 0})
        row["calls"] += 1
        row["successes"] += 1 if success else 0
        row["failures"] += 0 if success else 1
    def snapshot(self):
        avg = self.total_latency_ms / self.calls if self.calls else 0.0
        return {"calls": self.calls, "successes": self.successes, "failures": self.failures, "avg_latency_ms": avg, "by_provider": self.by_provider}

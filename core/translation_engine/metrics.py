"""Translation engine metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class TranslationMetrics:
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.observations: Dict[str, List[float]] = {}

    def increment(self, name: str, amount: int = 1) -> int:
        self.counters[name] = self.counters.get(name, 0) + amount
        return self.counters[name]

    def observe(self, name: str, value: float) -> None:
        self.observations.setdefault(name, []).append(float(value))

    def summary(self) -> Dict[str, Any]:
        obs: Dict[str, Any] = {}
        for name, values in self.observations.items():
            obs[name] = {"count": len(values), "min": min(values), "max": max(values), "avg": sum(values) / len(values)} if values else {"count": 0}
        return {"counters": dict(self.counters), "observations": obs}

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_metrics", "counters": dict(self.counters), "observation_keys": sorted(self.observations)}

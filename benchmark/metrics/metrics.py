from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MetricBag:
    values: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "MetricBag":
        self.values[key] = value
        return self

    def inc(self, key: str, amount: int | float = 1) -> "MetricBag":
        self.values[key] = self.values.get(key, 0) + amount
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.values)

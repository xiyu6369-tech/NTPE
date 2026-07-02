"""Runtime Resource response models for NTPE Stage-11.6."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .runtime_resource import RuntimeResource


@dataclass(frozen=True)
class RuntimeResourceListResponse:
    resources: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_resources(cls, resources: Iterable[RuntimeResource]) -> "RuntimeResourceListResponse":
        items = [resource.to_dict() for resource in resources]
        return cls(resources=items, count=len(items))

    def to_dict(self) -> Dict[str, Any]:
        return {"count": self.count, "resources": list(self.resources)}

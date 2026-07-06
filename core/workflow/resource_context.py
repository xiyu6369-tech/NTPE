# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .resource_profile import ResourceProfile


@dataclass
class ResourceContext:
    job_count: int = 1
    estimated_tokens: int = 0
    max_cost: float | None = None
    max_workers: int = 4
    cache_hit_rate: float = 0.0
    profiles: List[ResourceProfile] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_texts(
        cls,
        texts: Iterable[str],
        profiles: Iterable[ResourceProfile] | None = None,
        **kwargs: Any,
    ) -> "ResourceContext":
        items = list(texts)
        # Conservative character-to-token estimate for planning without provider calls.
        estimated_tokens = sum(max(1, len(item) // 2) for item in items)
        return cls(
            job_count=max(1, len(items)),
            estimated_tokens=estimated_tokens,
            profiles=list(profiles or []),
            **kwargs,
        )

    def normalized_cache_hit_rate(self) -> float:
        return min(1.0, max(0.0, float(self.cache_hit_rate)))

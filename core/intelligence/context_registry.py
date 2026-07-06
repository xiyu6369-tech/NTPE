# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .context_result import ContextItem


@dataclass
class ContextRegistry:
    """Named context buckets for runtime/session integration."""

    _buckets: Dict[str, List[ContextItem]] = field(default_factory=dict)

    def register(self, bucket: str, item: ContextItem) -> None:
        self._buckets.setdefault(bucket, []).append(item)

    def list_bucket(self, bucket: str) -> List[ContextItem]:
        return list(self._buckets.get(bucket, []))

    def list_all(self) -> List[ContextItem]:
        items: List[ContextItem] = []
        for bucket in sorted(self._buckets):
            items.extend(self._buckets[bucket])
        return items

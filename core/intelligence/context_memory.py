# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .context_result import ContextItem


@dataclass
class ContextMemory:
    """In-memory context cache with stable deterministic ordering."""

    _items: Dict[str, ContextItem] = field(default_factory=dict)

    def remember(self, item: ContextItem) -> None:
        self._items[item.item_id] = item

    def remember_many(self, items: Iterable[ContextItem]) -> None:
        for item in items:
            self.remember(item)

    def get(self, item_id: str) -> ContextItem | None:
        return self._items.get(item_id)

    def list_items(self) -> List[ContextItem]:
        return [self._items[key] for key in sorted(self._items)]

    def clear(self) -> None:
        self._items.clear()

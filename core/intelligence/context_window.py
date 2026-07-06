# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .context_exceptions import ContextWindowError
from .context_result import ContextItem


@dataclass
class ContextWindow:
    """Deterministic dynamic context window.

    This object intentionally avoids model calls. It provides a stable Stage-16.1
    core that can be bound to Runtime, Provider and Quality layers later.
    """

    max_items: int = 8
    max_chars: int = 4000
    items: List[ContextItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_items <= 0:
            raise ContextWindowError("max_items must be positive")
        if self.max_chars <= 0:
            raise ContextWindowError("max_chars must be positive")

    def add(self, item: ContextItem) -> None:
        if item.text.strip():
            self.items.append(item)
            self.items = self.select(self.items)

    def extend(self, items: Iterable[ContextItem]) -> None:
        for item in items:
            self.add(item)

    def select(self, items: Iterable[ContextItem]) -> List[ContextItem]:
        ordered = sorted(items, key=lambda item: (-item.priority, item.item_id))
        selected: List[ContextItem] = []
        total_chars = 0
        for item in ordered:
            next_len = len(item.text)
            if len(selected) >= self.max_items:
                break
            if total_chars + next_len > self.max_chars and selected:
                continue
            selected.append(item)
            total_chars += next_len
        return selected

    def compress(self) -> str:
        lines = []
        for item in self.items:
            text = " ".join(item.text.split())
            lines.append(f"[{item.source}:{item.item_id}] {text}")
        return "\n".join(lines)

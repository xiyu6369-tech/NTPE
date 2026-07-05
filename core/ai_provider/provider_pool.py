from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


@dataclass
class ProviderPoolEntry:
    name: str
    weight: float = 1.0
    priority: int = 100
    enabled: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "weight": self.weight,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


class ProviderPool:
    """Mutable provider pool for multi-provider orchestration."""

    def __init__(self, entries: Optional[Iterable[ProviderPoolEntry | str]] = None):
        self._entries: Dict[str, ProviderPoolEntry] = {}
        for entry in entries or []:
            self.add(entry)

    def add(self, entry: ProviderPoolEntry | str, weight: float = 1.0, priority: int = 100, enabled: bool = True) -> ProviderPoolEntry:
        if isinstance(entry, str):
            item = ProviderPoolEntry(entry, weight=weight, priority=priority, enabled=enabled)
        else:
            item = entry
        self._entries[item.name] = item
        return item

    def remove(self, name: str) -> None:
        self._entries.pop(name, None)

    def enable(self, name: str) -> None:
        self._entries[name].enabled = True

    def disable(self, name: str) -> None:
        self._entries[name].enabled = False

    def get(self, name: str) -> ProviderPoolEntry:
        return self._entries[name]

    def names(self, enabled_only: bool = True) -> List[str]:
        return [entry.name for entry in self.entries(enabled_only=enabled_only)]

    def entries(self, enabled_only: bool = True) -> List[ProviderPoolEntry]:
        values = list(self._entries.values())
        if enabled_only:
            values = [entry for entry in values if entry.enabled]
        return sorted(values, key=lambda item: (item.priority, item.name))

    def __iter__(self) -> Iterator[ProviderPoolEntry]:
        return iter(self.entries())

    def to_dict(self) -> Dict[str, object]:
        return {name: entry.to_dict() for name, entry in self._entries.items()}

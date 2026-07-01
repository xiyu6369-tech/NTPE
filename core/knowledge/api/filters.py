"""Foundation-08.5 Knowledge Query API filters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem


@dataclass
class KnowledgeFilter:
    """Composable item filter used by the Query API."""

    domain: Optional[str] = None
    keys: List[str] = field(default_factory=list)
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    predicate: Optional[Callable[[KnowledgeItem], bool]] = None

    def matches(self, item: KnowledgeItem) -> bool:
        if self.domain and item.domain != self.domain:
            return False
        if self.keys and item.key not in self.keys:
            return False
        if self.text:
            haystack = f"{item.key} {item.value} {item.domain}".lower()
            if self.text.lower() not in haystack:
                return False
        for key, value in self.metadata.items():
            if item.metadata.get(key) != value:
                return False
        if self.predicate and not self.predicate(item):
            return False
        return True

    def apply(self, items: Iterable[KnowledgeItem]) -> List[KnowledgeItem]:
        return [item for item in items if self.matches(item)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "keys": list(self.keys),
            "text": self.text,
            "metadata": dict(self.metadata),
            "predicate": bool(self.predicate),
        }


@dataclass
class KnowledgeSort:
    """Simple stable sorting strategy for query results."""

    field: str = "key"
    reverse: bool = False

    def apply(self, items: Iterable[KnowledgeItem]) -> List[KnowledgeItem]:
        def read(item: KnowledgeItem) -> Any:
            if hasattr(item, self.field):
                return getattr(item, self.field)
            return item.metadata.get(self.field)

        return sorted(list(items), key=lambda item: (read(item) is None, str(read(item))), reverse=self.reverse)

    def to_dict(self) -> Dict[str, Any]:
        return {"field": self.field, "reverse": self.reverse}


__all__ = ["KnowledgeFilter", "KnowledgeSort"]

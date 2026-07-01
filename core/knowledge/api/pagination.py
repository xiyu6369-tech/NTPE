"""Foundation-08.5 Knowledge Query API pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from ..contracts import KnowledgeItem


@dataclass
class KnowledgePagination:
    """Offset/limit pagination metadata."""

    offset: int = 0
    limit: int | None = None

    def apply(self, items: Iterable[KnowledgeItem]) -> Tuple[List[KnowledgeItem], Dict[str, Any]]:
        all_items = list(items)
        start = max(0, int(self.offset or 0))
        if self.limit is None:
            page = all_items[start:]
        else:
            page = all_items[start:start + max(0, int(self.limit))]
        return page, {
            "offset": start,
            "limit": self.limit,
            "total": len(all_items),
            "count": len(page),
            "has_more": start + len(page) < len(all_items),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"offset": self.offset, "limit": self.limit}


__all__ = ["KnowledgePagination"]

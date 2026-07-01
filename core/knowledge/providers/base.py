"""Foundation-08.1 provider base classes."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeProvider, KnowledgeQuery


class StaticKnowledgeProvider(KnowledgeProvider):
    """Simple provider for a single knowledge domain."""

    domain = "general"
    source = "static"

    def __init__(self, data: Optional[Dict[str, Any] | Iterable[Any]] = None, domain: Optional[str] = None, source: Optional[str] = None):
        self.domain = domain or self.domain
        self.source = source or self.source
        self.data = data if data is not None else {}

    def iter_items(self) -> List[KnowledgeItem]:
        items: List[KnowledgeItem] = []
        if isinstance(self.data, dict):
            for key, value in self.data.items():
                items.append(KnowledgeItem(key=str(key), value=value, domain=self.domain, source=self.source))
        else:
            for index, value in enumerate(self.data):
                key = str(value.get("key", index)) if isinstance(value, dict) else str(index)
                items.append(KnowledgeItem(key=key, value=value, domain=self.domain, source=self.source))
        return items

    def provide(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        return [item for item in self.iter_items() if query.matches(item)]

    def build_context(self, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        query = query or KnowledgeQuery(domain=self.domain)
        items = self.provide(query)
        return {
            "type": "knowledge_provider_context",
            "version": "foundation-08.1",
            "domain": self.domain,
            "items": [item.to_dict() for item in items],
        }


__all__ = ["StaticKnowledgeProvider"]

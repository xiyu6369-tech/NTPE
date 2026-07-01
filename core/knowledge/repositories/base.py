"""Foundation-08.1 Knowledge Repository base helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeManifest, KnowledgeQuery, KnowledgeRepository, KnowledgeSnapshot


class RepositoryMixin:
    """Convenience helpers shared by concrete Knowledge repositories."""

    def put_value(
        self,
        key: str,
        value: Any,
        domain: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> KnowledgeItem:
        item = KnowledgeItem(key=str(key), value=value, domain=domain, metadata=dict(metadata or {}), source=source)
        return self.put(item)  # type: ignore[attr-defined]

    def put_many(self, items: Iterable[KnowledgeItem]) -> List[KnowledgeItem]:
        return [self.put(item) for item in items]  # type: ignore[attr-defined]

    def query_values(self, query: KnowledgeQuery) -> List[Any]:
        return [item.value for item in self.query(query)]  # type: ignore[attr-defined]

    def to_context(self, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        query = query or KnowledgeQuery()
        items = self.query(query)  # type: ignore[attr-defined]
        domains: Dict[str, Dict[str, Any]] = {}
        for item in items:
            domains.setdefault(item.domain, {})[item.key] = item.value
        return {
            "type": "knowledge_repository_context",
            "version": "foundation-08.1",
            "items": [item.to_dict() for item in items],
            "domains": domains,
        }


__all__ = [
    "KnowledgeItem",
    "KnowledgeManifest",
    "KnowledgeQuery",
    "KnowledgeRepository",
    "KnowledgeSnapshot",
    "RepositoryMixin",
]

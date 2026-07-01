"""Foundation-08.5 Knowledge Query Builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..contracts import KnowledgeQuery
from .filters import KnowledgeFilter, KnowledgeSort
from .pagination import KnowledgePagination


@dataclass
class KnowledgeQueryRequest:
    """Execution-ready query request used by the Query API."""

    query: KnowledgeQuery = field(default_factory=KnowledgeQuery)
    filter: KnowledgeFilter = field(default_factory=KnowledgeFilter)
    sort: Optional[KnowledgeSort] = None
    pagination: KnowledgePagination = field(default_factory=KnowledgePagination)
    include_context: bool = False
    include_snapshot: bool = False
    use_cache: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "filter": self.filter.to_dict(),
            "sort": self.sort.to_dict() if self.sort else None,
            "pagination": self.pagination.to_dict(),
            "include_context": self.include_context,
            "include_snapshot": self.include_snapshot,
            "use_cache": self.use_cache,
            "metadata": dict(self.metadata),
        }


class KnowledgeQueryBuilder:
    """Fluent builder for KnowledgeQueryRequest."""

    def __init__(self):
        self._text = ""
        self._domain: Optional[str] = None
        self._keys: List[str] = []
        self._limit: Optional[int] = None
        self._metadata: Dict[str, Any] = {}
        self._filter_metadata: Dict[str, Any] = {}
        self._sort: Optional[KnowledgeSort] = None
        self._pagination = KnowledgePagination()
        self._include_context = False
        self._include_snapshot = False
        self._use_cache = True

    def text(self, value: str) -> "KnowledgeQueryBuilder":
        self._text = value or ""
        return self

    def domain(self, value: Optional[str]) -> "KnowledgeQueryBuilder":
        self._domain = value
        return self

    def keys(self, *values: str) -> "KnowledgeQueryBuilder":
        self._keys = [str(value) for value in values if value is not None]
        return self

    def limit(self, value: Optional[int]) -> "KnowledgeQueryBuilder":
        self._limit = value
        self._pagination.limit = value
        return self

    def metadata(self, **values: Any) -> "KnowledgeQueryBuilder":
        self._metadata.update(values)
        return self

    def filter_metadata(self, **values: Any) -> "KnowledgeQueryBuilder":
        self._filter_metadata.update(values)
        return self

    def sort_by(self, field: str = "key", reverse: bool = False) -> "KnowledgeQueryBuilder":
        self._sort = KnowledgeSort(field=field, reverse=reverse)
        return self

    def paginate(self, offset: int = 0, limit: Optional[int] = None) -> "KnowledgeQueryBuilder":
        self._pagination = KnowledgePagination(offset=offset, limit=limit)
        return self

    def with_context(self, enabled: bool = True) -> "KnowledgeQueryBuilder":
        self._include_context = enabled
        return self

    def with_snapshot(self, enabled: bool = True) -> "KnowledgeQueryBuilder":
        self._include_snapshot = enabled
        return self

    def cache(self, enabled: bool = True) -> "KnowledgeQueryBuilder":
        self._use_cache = enabled
        return self

    def build(self) -> KnowledgeQueryRequest:
        query = KnowledgeQuery(text=self._text, domain=self._domain, keys=list(self._keys), limit=self._limit, metadata=dict(self._metadata))
        query_filter = KnowledgeFilter(domain=self._domain, keys=list(self._keys), text=self._text, metadata=dict(self._filter_metadata or self._metadata))
        return KnowledgeQueryRequest(
            query=query,
            filter=query_filter,
            sort=self._sort,
            pagination=self._pagination,
            include_context=self._include_context,
            include_snapshot=self._include_snapshot,
            use_cache=self._use_cache,
            metadata={"builder": "foundation-08.5"},
        )


def build_query_request(**kwargs: Any) -> KnowledgeQueryRequest:
    builder = KnowledgeQueryBuilder()
    if "text" in kwargs:
        builder.text(kwargs["text"])
    if "domain" in kwargs:
        builder.domain(kwargs["domain"])
    if "keys" in kwargs:
        builder.keys(*kwargs.get("keys") or [])
    if "limit" in kwargs:
        builder.limit(kwargs["limit"])
    return builder.build()


__all__ = ["KnowledgeQueryBuilder", "KnowledgeQueryRequest", "build_query_request"]

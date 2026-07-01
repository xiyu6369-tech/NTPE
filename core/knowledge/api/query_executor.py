"""Foundation-08.5 Knowledge Query Executor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery, KnowledgeSnapshot
from ..repositories.manager import KnowledgeRepositoryManager
from ..cache.cache_manager import KnowledgeCacheManager
from .query_builder import KnowledgeQueryRequest


@dataclass
class KnowledgeQueryResult:
    """Stable response envelope returned by the Query API."""

    items: List[KnowledgeItem] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    snapshot: Optional[KnowledgeSnapshot] = None
    pagination: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "context": dict(self.context),
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "pagination": dict(self.pagination),
            "metadata": dict(self.metadata),
        }


class KnowledgeQueryExecutor:
    """Execute query requests against repository and optional cache layers."""

    version = "foundation-08.5"

    def __init__(
        self,
        manager: Optional[KnowledgeRepositoryManager] = None,
        cache_manager: Optional[KnowledgeCacheManager] = None,
        event_bus: Any = None,
    ):
        self.manager = manager or KnowledgeRepositoryManager()
        self.cache_manager = cache_manager
        self.event_bus = event_bus

    def _publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.event_bus is None:
            return
        data = {"version": self.version, **dict(payload or {})}
        if hasattr(self.event_bus, "publish"):
            try:
                self.event_bus.publish(event_type, data)
            except TypeError:
                self.event_bus.publish({"event_type": event_type, "payload": data})

    def _repository_query(self, query: KnowledgeQuery, use_cache: bool = True) -> List[KnowledgeItem]:
        if use_cache and self.cache_manager is not None:
            return self.cache_manager.query(query)
        return self.manager.query(query)

    def execute(self, request: KnowledgeQueryRequest | KnowledgeQuery | Dict[str, Any] | None = None) -> KnowledgeQueryResult:
        if request is None:
            request = KnowledgeQueryRequest()
        if isinstance(request, KnowledgeQuery):
            request = KnowledgeQueryRequest(query=request)
        if isinstance(request, dict):
            request = KnowledgeQueryRequest(query=KnowledgeQuery.from_dict(request))

        items = self._repository_query(request.query, use_cache=request.use_cache)
        items = request.filter.apply(items)
        if request.sort:
            items = request.sort.apply(items)
        page_items, pagination = request.pagination.apply(items)

        context: Dict[str, Any] = {}
        if request.include_context:
            context = self.manager.build_context(request.query)
        snapshot: Optional[KnowledgeSnapshot] = None
        if request.include_snapshot:
            if request.use_cache and self.cache_manager is not None:
                snapshot = self.cache_manager.snapshot("query_api")
            else:
                snapshot = self.manager.snapshot("query_api")

        result = KnowledgeQueryResult(
            items=page_items,
            context=context,
            snapshot=snapshot,
            pagination=pagination,
            metadata={
                "version": self.version,
                "cache_enabled": bool(request.use_cache and self.cache_manager is not None),
                "query": request.query.to_dict(),
            },
        )
        self._publish("KnowledgeQueryExecuted", {"item_count": len(page_items), "total": pagination.get("total")})
        return result


__all__ = ["KnowledgeQueryExecutor", "KnowledgeQueryResult"]

"""Foundation-08.5 Knowledge Query API facade."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager
from ..cache.cache_manager import KnowledgeCacheManager
from .manifest import build_knowledge_api_manifest
from .query_builder import KnowledgeQueryBuilder, KnowledgeQueryRequest
from .query_executor import KnowledgeQueryExecutor, KnowledgeQueryResult


class KnowledgeAPI:
    """Public, cache-aware query facade for Runtime, Prompt, Plugin, and SDK callers."""

    version = "foundation-08.5"

    def __init__(
        self,
        manager: Optional[KnowledgeRepositoryManager] = None,
        cache_manager: Optional[KnowledgeCacheManager] = None,
        event_bus: Any = None,
    ):
        self.manager = manager or KnowledgeRepositoryManager()
        self.cache_manager = cache_manager
        self.executor = KnowledgeQueryExecutor(manager=self.manager, cache_manager=self.cache_manager, event_bus=event_bus)
        self.event_bus = event_bus

    def builder(self) -> KnowledgeQueryBuilder:
        return KnowledgeQueryBuilder()

    def query(self, request: KnowledgeQueryRequest | KnowledgeQuery | Dict[str, Any] | None = None, **kwargs: Any) -> KnowledgeQueryResult:
        if request is None and kwargs:
            builder = self.builder()
            if "text" in kwargs:
                builder.text(kwargs["text"])
            if "domain" in kwargs:
                builder.domain(kwargs["domain"])
            if "keys" in kwargs:
                builder.keys(*kwargs.get("keys") or [])
            if "limit" in kwargs:
                builder.limit(kwargs["limit"])
            if "offset" in kwargs or "page_limit" in kwargs:
                builder.paginate(offset=kwargs.get("offset", 0), limit=kwargs.get("page_limit"))
            request = builder.build()
        return self.executor.execute(request)

    def get(self, key: str, domain: str = "general") -> Optional[KnowledgeItem]:
        result = self.query(self.builder().domain(domain).keys(key).limit(1).build())
        return result.items[0] if result.items else None

    def search(self, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> List[KnowledgeItem]:
        return self.query(self.builder().text(text).domain(domain).limit(limit).build()).items

    def runtime_query(self, segment: Any = None, domain: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        request = self.builder().domain(domain).limit(limit).with_context(True).with_snapshot(True).build()
        result = self.query(request)
        payload = result.to_dict()
        payload["type"] = "knowledge_runtime_query"
        payload["segment_id"] = getattr(segment, "id", None) or getattr(segment, "segment_id", None) or (segment.get("id") if isinstance(segment, dict) else None)
        return payload

    def prompt_query(self, prompt_package: Optional[Dict[str, Any]] = None, domain: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        package = dict(prompt_package or {})
        result = self.query(self.builder().domain(domain).limit(limit).with_context(True).build())
        components = list(package.get("context_components", []))
        components.append({"type": "knowledge_query_api", "version": self.version, "result": result.to_dict()})
        package["context_components"] = components
        return package

    def plugin_query(self, plugin_name: str = "plugin", query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        result = self.query(query or KnowledgeQuery())
        return {"plugin": plugin_name, "version": self.version, "result": result.to_dict()}

    def cache_query(self, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        result = self.query(KnowledgeQueryRequest(query=query or KnowledgeQuery(), use_cache=True))
        metrics = self.cache_manager.metrics() if self.cache_manager is not None else {}
        return {"result": result.to_dict(), "cache_metrics": metrics}

    def snapshot_query(self, name: str = "api") -> Dict[str, Any]:
        snapshot = self.cache_manager.snapshot(name) if self.cache_manager is not None else self.manager.snapshot(name)
        return snapshot.to_dict()

    def put(self, key: str, value: Any, domain: str = "general", **metadata: Any) -> KnowledgeItem:
        item = KnowledgeItem(key=key, value=value, domain=domain, metadata=dict(metadata), source="knowledge_api")
        if self.cache_manager is not None:
            return self.cache_manager.put_item(item)
        return self.manager.repository.put(item)

    def put_many(self, items: Iterable[KnowledgeItem | Dict[str, Any]]) -> List[KnowledgeItem]:
        normalized = [item if isinstance(item, KnowledgeItem) else KnowledgeItem.from_dict(item) for item in items]
        if self.cache_manager is not None:
            return self.cache_manager.ingest_items(normalized)
        return self.manager.ingest_items(normalized)

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = build_knowledge_api_manifest(metadata)
        manifest["repository"] = self.manager.repository.manifest().to_dict()
        if self.cache_manager is not None:
            manifest["cache"] = self.cache_manager.manifest()
        return manifest

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


__all__ = ["KnowledgeAPI"]

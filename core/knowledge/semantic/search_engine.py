"""Foundation-08.6 semantic search runtime facade."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..api.knowledge_api import KnowledgeAPI
from ..cache.cache_manager import KnowledgeCacheManager
from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager
from .index_builder import KnowledgeIndexBuilder
from .manifest import build_knowledge_semantic_manifest
from .ranking import KnowledgeSearchResult
from .semantic_index import KnowledgeSemanticIndex


class KnowledgeSemanticSearchEngine:
    """Cache-aware semantic search facade for Runtime, Prompt, and API callers."""

    version = "foundation-08.6"

    def __init__(
        self,
        manager: Optional[KnowledgeRepositoryManager] = None,
        cache_manager: Optional[KnowledgeCacheManager] = None,
        index: Optional[KnowledgeSemanticIndex] = None,
        event_bus: Any = None,
    ):
        self.manager = manager or KnowledgeRepositoryManager()
        self.cache_manager = cache_manager
        self.index = index or KnowledgeIndexBuilder(self.manager).from_repository(self.manager)
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

    def rebuild(self) -> KnowledgeSemanticIndex:
        self.index = KnowledgeIndexBuilder(self.manager).from_repository(self.manager)
        self._publish("KnowledgeSemanticIndexRebuilt", {"document_count": self.index.manifest()["metadata"]["document_count"]})
        return self.index

    def ingest_items(self, items: Iterable[KnowledgeItem | Dict[str, Any]], update_repository: bool = True) -> List[KnowledgeItem]:
        normalized = [item if isinstance(item, KnowledgeItem) else KnowledgeItem.from_dict(item) for item in items]
        if update_repository:
            if self.cache_manager is not None:
                self.cache_manager.ingest_items(normalized)
            else:
                self.manager.ingest_items(normalized)
        self.index.add_many(normalized)
        self._publish("KnowledgeSemanticIndexed", {"item_count": len(normalized)})
        return normalized

    def search(self, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> List[KnowledgeSearchResult]:
        results = self.index.search(text=text, domain=domain, limit=limit)
        self._publish("KnowledgeSemanticSearched", {"text": text, "domain": domain, "result_count": len(results)})
        return results

    def hybrid_search(self, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> List[KnowledgeSearchResult]:
        semantic_results = self.search(text=text, domain=domain, limit=None)
        seen = {(result.item.domain, result.item.key) for result in semantic_results}
        api = KnowledgeAPI(manager=self.manager, cache_manager=self.cache_manager)
        keyword_items = api.search(text=text, domain=domain, limit=None)
        merged = list(semantic_results)
        for item in keyword_items:
            identity = (item.domain, item.key)
            if identity not in seen:
                merged.append(KnowledgeSearchResult(item=item, score=0.5, matched_tokens=[], metadata={"source": "keyword"}))
                seen.add(identity)
        ranked = self.index.ranking.rank(merged, limit=limit)
        self._publish("KnowledgeHybridSearched", {"text": text, "domain": domain, "result_count": len(ranked)})
        return ranked

    def runtime_semantic_query(self, segment: Any = None, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        results = self.hybrid_search(text=text, domain=domain, limit=limit)
        segment_id = getattr(segment, "id", None) or getattr(segment, "segment_id", None) or (segment.get("id") if isinstance(segment, dict) else None)
        return {"type": "knowledge_runtime_semantic_query", "version": self.version, "segment_id": segment_id, "results": [result.to_dict() for result in results]}

    def prompt_semantic_context(self, prompt_package: Optional[Dict[str, Any]] = None, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        package = dict(prompt_package or {})
        components = list(package.get("context_components", []))
        components.append({"type": "knowledge_semantic_context", "version": self.version, "results": [result.to_dict() for result in self.hybrid_search(text=text, domain=domain, limit=limit)]})
        package["context_components"] = components
        return package

    def cache_semantic_query(self, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        results = self.hybrid_search(text=text, domain=domain, limit=limit)
        metrics = self.cache_manager.metrics() if self.cache_manager is not None else {}
        return {"results": [result.to_dict() for result in results], "cache_metrics": metrics}

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = build_knowledge_semantic_manifest(metadata)
        manifest["index"] = self.index.manifest()
        return manifest

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


__all__ = ["KnowledgeSemanticSearchEngine"]

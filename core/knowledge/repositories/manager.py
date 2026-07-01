"""Foundation-08.1 Knowledge Repository Manager."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeProvider, KnowledgeQuery, KnowledgeSnapshot
from .memory_repository import KnowledgeMemoryRepository


class KnowledgeRepositoryManager:
    """Coordinate repositories and providers without coupling Runtime to storage."""

    def __init__(self, repository: Optional[KnowledgeMemoryRepository] = None):
        self.repository = repository or KnowledgeMemoryRepository(metadata={"manager": "knowledge_repository_manager"})
        self.providers: Dict[str, KnowledgeProvider] = {}

    def register_provider(self, name: str, provider: KnowledgeProvider, ingest: bool = True) -> None:
        if not name:
            raise ValueError("provider name is required")
        self.providers[name] = provider
        if ingest:
            self.ingest_provider(name)

    def ingest_provider(self, name: str, query: Optional[KnowledgeQuery] = None) -> List[KnowledgeItem]:
        provider = self.providers[name]
        items = provider.provide(query or KnowledgeQuery())
        for item in items:
            self.repository.put(item)
        return items

    def ingest_items(self, items: Iterable[KnowledgeItem]) -> List[KnowledgeItem]:
        return self.repository.put_many(items)

    def get(self, key: str, domain: str = "general") -> Optional[KnowledgeItem]:
        return self.repository.get(key, domain)

    def query(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        return self.repository.query(query)

    def build_context(self, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        return self.repository.to_context(query)

    def snapshot(self, name: str = "manager") -> KnowledgeSnapshot:
        return self.repository.snapshot(name)

    def restore(self, snapshot: KnowledgeSnapshot | Dict[str, Any]) -> "KnowledgeRepositoryManager":
        self.repository.load_snapshot(snapshot)
        return self

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append({
            "name": "knowledge_repository",
            "version": "foundation-08.1",
            "enabled": True,
            "manifest": self.repository.manifest().to_dict(),
            "providers": sorted(self.providers.keys()),
        })
        next_manifest["components"] = components
        return next_manifest

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_package = dict(prompt_package or {})
        components = list(next_package.get("context_components", []))
        components.append(self.build_context())
        next_package["context_components"] = components
        return next_package


__all__ = ["KnowledgeRepositoryManager"]

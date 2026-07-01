"""Foundation-08.0 Knowledge Provider."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .contracts import KnowledgeItem, KnowledgeProvider, KnowledgeQuery
from .repository import InMemoryKnowledgeRepository


class RepositoryKnowledgeProvider(KnowledgeProvider):
    """Read-only provider facade for Runtime, Prompt Pipeline, and Plugins."""

    def __init__(self, repository: Optional[InMemoryKnowledgeRepository] = None):
        self.repository = repository or InMemoryKnowledgeRepository()

    def provide(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        return self.repository.query(query)

    def build_context(self, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        query = query or KnowledgeQuery()
        items = self.provide(query)
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in items:
            grouped.setdefault(item.domain, {})[item.key] = item.value
        return {
            "type": "knowledge_context",
            "version": "foundation-08.0",
            "items": [item.to_dict() for item in items],
            "domains": grouped,
            "manifest": self.repository.manifest().to_dict(),
        }

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_package = dict(prompt_package or {})
        components = list(next_package.get("context_components", []))
        components.append(self.build_context())
        next_package["context_components"] = components
        return next_package

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append({
            "name": "knowledge_layer_contract",
            "version": "foundation-08.0",
            "enabled": True,
            "manifest": self.repository.manifest().to_dict(),
        })
        next_manifest["components"] = components
        return next_manifest


__all__ = ["RepositoryKnowledgeProvider"]

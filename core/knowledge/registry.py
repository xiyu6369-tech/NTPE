"""Foundation-08.0 Knowledge Repository Registry."""

from __future__ import annotations

from typing import Dict, List, Optional

from .contracts import KnowledgeRegistryContract, KnowledgeRepository
from .repository import InMemoryKnowledgeRepository


class KnowledgeRegistry(KnowledgeRegistryContract):
    def __init__(self):
        self._repositories: Dict[str, KnowledgeRepository] = {}
        self._default_name: Optional[str] = None

    def register(self, name: str, repository: KnowledgeRepository, default: bool = False) -> None:
        if not name:
            raise ValueError("repository name is required")
        self._repositories[name] = repository
        if default or self._default_name is None:
            self._default_name = name

    def get(self, name: Optional[str] = None) -> KnowledgeRepository:
        lookup = name or self._default_name
        if lookup is None or lookup not in self._repositories:
            raise KeyError("knowledge repository is not registered")
        return self._repositories[lookup]

    def list(self) -> List[str]:
        return sorted(self._repositories.keys())


def get_default_knowledge_registry() -> KnowledgeRegistry:
    registry = KnowledgeRegistry()
    registry.register("memory", InMemoryKnowledgeRepository(), default=True)
    return registry


__all__ = ["KnowledgeRegistry", "get_default_knowledge_registry"]

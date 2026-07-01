"""Foundation-08.1 concrete in-memory repository implementation."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ..contracts import KnowledgeItem, KnowledgeManifest
from ..repository import InMemoryKnowledgeRepository
from .base import RepositoryMixin


class KnowledgeMemoryRepository(RepositoryMixin, InMemoryKnowledgeRepository):
    """Foundation-08.1 repository used by managers and providers.

    It extends the 08.0 in-memory repository without changing its public
    behavior, so existing 08.0 callers remain compatible.
    """

    version = "foundation-08.1"

    def __init__(self, items: Optional[Iterable[KnowledgeItem]] = None, metadata: Optional[Dict[str, Any]] = None):
        merged_metadata: Dict[str, Any] = {"foundation": "08.1"}
        merged_metadata.update(dict(metadata or {}))
        super().__init__(items=items, metadata=merged_metadata)

    def manifest(self) -> KnowledgeManifest:
        base = super().manifest().to_dict()
        metadata = dict(base.get("metadata") or {})
        metadata.update({"repository_version": self.version, "storage": "memory"})
        return KnowledgeManifest(
            name="knowledge_memory_repository",
            version=self.version,
            capabilities=list(base.get("capabilities") or []) + ["put_many", "context", "provider_ingest"],
            metadata=metadata,
        )


def build_memory_repository(**metadata: Any) -> KnowledgeMemoryRepository:
    return KnowledgeMemoryRepository(metadata=metadata)


__all__ = ["KnowledgeMemoryRepository", "build_memory_repository"]

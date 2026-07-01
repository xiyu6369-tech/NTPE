"""Foundation-08.6 semantic index builder."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ..contracts import KnowledgeItem, KnowledgeSnapshot
from ..repositories.manager import KnowledgeRepositoryManager
from .semantic_index import KnowledgeSemanticIndex


class KnowledgeIndexBuilder:
    """Build semantic indexes from repository managers, snapshots, or iterables."""

    version = "foundation-08.6"

    def __init__(self, manager: Optional[KnowledgeRepositoryManager] = None):
        self.manager = manager

    def from_items(self, items: Iterable[KnowledgeItem | dict[str, Any]]) -> KnowledgeSemanticIndex:
        return KnowledgeSemanticIndex(metadata={"builder": self.version}).build(items)

    def from_snapshot(self, snapshot: KnowledgeSnapshot | dict[str, Any]) -> KnowledgeSemanticIndex:
        knowledge_snapshot = snapshot if isinstance(snapshot, KnowledgeSnapshot) else KnowledgeSnapshot.from_dict(snapshot)
        index = self.from_items(knowledge_snapshot.items)
        index.metadata.update({"snapshot": knowledge_snapshot.name, "snapshot_version": knowledge_snapshot.version})
        return index

    def from_repository(self, manager: Optional[KnowledgeRepositoryManager] = None) -> KnowledgeSemanticIndex:
        active_manager = manager or self.manager or KnowledgeRepositoryManager()
        return self.from_snapshot(active_manager.snapshot("semantic_index"))


__all__ = ["KnowledgeIndexBuilder"]

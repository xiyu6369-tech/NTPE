"""Foundation-08.1 persistence adapter helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeSnapshot
from ..repositories.memory_repository import KnowledgeMemoryRepository


class PersistenceKnowledgeAdapter:
    """Tolerant adapter for JSON/SQLite style snapshot payloads."""

    def __init__(self, repository: Optional[KnowledgeMemoryRepository] = None):
        self.repository = repository or KnowledgeMemoryRepository(metadata={"adapter": "persistence"})

    def load(self, payload: Dict[str, Any] | KnowledgeSnapshot) -> KnowledgeMemoryRepository:
        if isinstance(payload, KnowledgeSnapshot):
            snapshot = payload
        else:
            snapshot = KnowledgeSnapshot.from_dict(payload)
        self.repository.load_snapshot(snapshot)
        return self.repository

    def dump(self, name: str = "knowledge_persistence") -> Dict[str, Any]:
        return self.repository.snapshot(name).to_dict()


__all__ = ["PersistenceKnowledgeAdapter"]

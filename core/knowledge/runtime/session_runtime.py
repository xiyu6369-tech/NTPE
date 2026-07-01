"""Foundation-08.2 Knowledge Session Runtime."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..contracts import KnowledgeSnapshot
from ..repositories.manager import KnowledgeRepositoryManager


class KnowledgeSessionRuntime:
    """Manage Knowledge Repository state across a runtime session."""

    version = "foundation-08.2"

    def __init__(self, session_id: str = "default", manager: Optional[KnowledgeRepositoryManager] = None):
        self.session_id = session_id
        self.manager = manager or KnowledgeRepositoryManager()
        self.history: List[Dict[str, Any]] = []

    def checkpoint(self, name: str = "checkpoint", metadata: Optional[Dict[str, Any]] = None) -> KnowledgeSnapshot:
        snapshot = self.manager.snapshot(name)
        snapshot.metadata.update({"session_id": self.session_id, **dict(metadata or {})})
        self.history.append(snapshot.to_dict())
        return snapshot

    def restore(self, snapshot: KnowledgeSnapshot | Dict[str, Any]) -> "KnowledgeSessionRuntime":
        self.manager.restore(snapshot)
        if isinstance(snapshot, KnowledgeSnapshot):
            self.history.append(snapshot.to_dict())
        else:
            self.history.append(dict(snapshot))
        return self

    def build_session_payload(self) -> Dict[str, Any]:
        return {
            "type": "knowledge_session_runtime",
            "version": self.version,
            "session_id": self.session_id,
            "history_count": len(self.history),
            "manifest": self.manager.repository.manifest().to_dict(),
        }


__all__ = ["KnowledgeSessionRuntime"]

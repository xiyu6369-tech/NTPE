"""Foundation-08.2 Knowledge Repository Runtime."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery, KnowledgeSnapshot
from ..repositories.manager import KnowledgeRepositoryManager
from .context_runtime import KnowledgeContextRuntime


class KnowledgeRepositoryRuntime:
    """Runtime facade that reads and updates the Knowledge Repository."""

    version = "foundation-08.2"

    def __init__(self, manager: Optional[KnowledgeRepositoryManager] = None):
        self.manager = manager or KnowledgeRepositoryManager()
        self.context_runtime = KnowledgeContextRuntime(self.manager)

    def before_segment(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        next_payload = self.context_runtime.attach_to_payload(payload, segment=segment, query=query)
        next_payload["knowledge_repository_runtime"] = {"phase": "before_segment", "version": self.version}
        return next_payload

    def update_from_items(self, items: Optional[Iterable[KnowledgeItem]] = None) -> int:
        if not items:
            return 0
        return len(self.manager.ingest_items(items))

    def update_from_payload(self, payload: Optional[Dict[str, Any]] = None) -> int:
        payload = payload or {}
        raw_items = payload.get("knowledge_items") or []
        items = [item if isinstance(item, KnowledgeItem) else KnowledgeItem.from_dict(item) for item in raw_items]
        return self.update_from_items(items)

    def after_segment(self, segment: Any = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        updated = self.update_from_payload(result)
        snapshot = self.manager.snapshot("runtime_after_segment")
        return {
            "type": "knowledge_repository_runtime_result",
            "version": self.version,
            "segment_id": self.context_runtime.resolve_segment_id(segment, result),
            "updated_count": updated,
            "snapshot": snapshot.to_dict(),
        }

    def snapshot(self, name: str = "knowledge_runtime") -> KnowledgeSnapshot:
        return self.manager.snapshot(name)


__all__ = ["KnowledgeRepositoryRuntime"]

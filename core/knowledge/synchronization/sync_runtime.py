"""Foundation-08.3 runtime synchronization facade."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeItem
from ..runtime.runtime import KnowledgeRuntime
from .sync_context import KnowledgeSyncContext


class KnowledgeSyncRuntime:
    """Apply synchronization results to KnowledgeRuntime-compatible objects."""

    version = "foundation-08.3"

    def __init__(self, runtime: Optional[KnowledgeRuntime] = None):
        self.runtime = runtime or KnowledgeRuntime()

    def pull_runtime_context(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.runtime.before_segment(segment=segment, payload=payload)

    def push_items(self, context: KnowledgeSyncContext) -> Dict[str, Any]:
        updated = []
        for item in context.items:
            if isinstance(item, KnowledgeItem):
                updated.append(self.runtime.ingest_value(item.key, item.value, domain=item.domain, source=item.source or context.source).to_dict())
        return {
            "type": "knowledge_sync_runtime_result",
            "version": self.version,
            "updated_count": len(updated),
            "items": updated,
            "context": context.to_dict(),
        }

    def checkpoint(self, context: KnowledgeSyncContext) -> Dict[str, Any]:
        return self.runtime.after_segment(segment={"id": context.segment_id}, result={"knowledge_sync": context.to_dict()})


__all__ = ["KnowledgeSyncRuntime"]

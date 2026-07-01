"""Foundation-08.3 synchronization context contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..contracts import KnowledgeItem, utc_now_iso


@dataclass
class KnowledgeSyncContext:
    """Runtime-safe synchronization payload.

    The context is intentionally dictionary-friendly so Runtime, Repository,
    Persistence, and Event Bus integrations can adopt it without depending on a
    concrete storage backend.
    """

    session_id: str = "default"
    segment_id: str = "default"
    direction: str = "bidirectional"
    source: str = "knowledge_runtime"
    items: List[KnowledgeItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def add_item(self, item: KnowledgeItem) -> KnowledgeItem:
        self.items.append(item)
        return item

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "segment_id": self.segment_id,
            "direction": self.direction,
            "source": self.source,
            "items": [item.to_dict() for item in self.items],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "KnowledgeSyncContext":
        payload = payload or {}
        return cls(
            session_id=str(payload.get("session_id", "default")),
            segment_id=str(payload.get("segment_id", "default")),
            direction=str(payload.get("direction", "bidirectional")),
            source=str(payload.get("source", "knowledge_runtime")),
            items=[KnowledgeItem.from_dict(item) for item in payload.get("items", [])],
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or utc_now_iso()),
        )


def build_sync_context(segment: Any = None, payload: Optional[Dict[str, Any]] = None, **metadata: Any) -> KnowledgeSyncContext:
    data = dict(payload or {})
    segment_id = str(
        data.get("segment_id")
        or getattr(segment, "segment_id", None)
        or getattr(segment, "id", None)
        or metadata.pop("segment_id", "default")
    )
    session_id = str(data.get("session_id") or metadata.pop("session_id", "default"))
    return KnowledgeSyncContext(
        session_id=session_id,
        segment_id=segment_id,
        direction=str(data.get("direction", metadata.pop("direction", "bidirectional"))),
        source=str(data.get("source", metadata.pop("source", "knowledge_runtime"))),
        metadata={**data.get("metadata", {}), **metadata},
    )


__all__ = ["KnowledgeSyncContext", "build_sync_context"]

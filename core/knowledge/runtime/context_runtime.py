"""Foundation-08.2 Knowledge Context Runtime."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager


class KnowledgeContextRuntime:
    """Build segment-safe knowledge context from a repository manager."""

    version = "foundation-08.2"

    def __init__(self, manager: Optional[KnowledgeRepositoryManager] = None):
        self.manager = manager or KnowledgeRepositoryManager()

    def resolve_segment_id(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None) -> str:
        if isinstance(payload, dict) and payload.get("segment_id") is not None:
            return str(payload.get("segment_id"))
        if isinstance(segment, dict):
            return str(segment.get("id") or segment.get("segment_id") or "segment")
        return str(getattr(segment, "id", getattr(segment, "segment_id", "segment")))

    def build_context(
        self,
        segment: Any = None,
        query: Optional[KnowledgeQuery] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        repository_context = self.manager.build_context(query or KnowledgeQuery())
        return {
            "type": "knowledge_runtime_context",
            "version": self.version,
            "segment_id": self.resolve_segment_id(segment, payload),
            "repository": repository_context,
            "domains": dict(repository_context.get("domains") or {}),
            "items": list(repository_context.get("items") or []),
        }

    def attach_to_payload(
        self,
        payload: Optional[Dict[str, Any]] = None,
        segment: Any = None,
        query: Optional[KnowledgeQuery] = None,
    ) -> Dict[str, Any]:
        next_payload = dict(payload or {})
        next_payload["knowledge_context"] = self.build_context(segment=segment, query=query, payload=next_payload)
        return next_payload


__all__ = ["KnowledgeContextRuntime"]

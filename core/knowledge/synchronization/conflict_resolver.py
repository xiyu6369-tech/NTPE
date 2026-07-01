"""Foundation-08.3 conflict resolution helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeItem, utc_now_iso


class KnowledgeConflictResolver:
    """Resolve KnowledgeItem conflicts using deterministic strategies."""

    version = "foundation-08.3"

    def __init__(self, strategy: str = "latest"):
        self.strategy = strategy

    def has_conflict(self, current: Optional[KnowledgeItem], incoming: Optional[KnowledgeItem]) -> bool:
        if current is None or incoming is None:
            return False
        return current.domain == incoming.domain and current.key == incoming.key and current.value != incoming.value

    def resolve(self, current: Optional[KnowledgeItem], incoming: KnowledgeItem, strategy: Optional[str] = None) -> KnowledgeItem:
        selected_strategy = strategy or self.strategy
        if current is None:
            return incoming
        if not self.has_conflict(current, incoming):
            return incoming
        if selected_strategy == "keep_existing":
            return current
        if selected_strategy == "merge_metadata":
            metadata: Dict[str, Any] = dict(current.metadata)
            metadata.update(incoming.metadata)
            metadata["conflict_resolved"] = True
            metadata["conflict_strategy"] = selected_strategy
            return KnowledgeItem(
                key=incoming.key,
                value=incoming.value,
                domain=incoming.domain,
                metadata=metadata,
                source=incoming.source or current.source,
                updated_at=incoming.updated_at or utc_now_iso(),
            )
        metadata = dict(incoming.metadata)
        metadata["conflict_resolved"] = True
        metadata["conflict_strategy"] = selected_strategy
        return KnowledgeItem(
            key=incoming.key,
            value=incoming.value,
            domain=incoming.domain,
            metadata=metadata,
            source=incoming.source,
            updated_at=incoming.updated_at or utc_now_iso(),
        )

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_conflict_resolver",
            "version": self.version,
            "strategy": self.strategy,
            "capabilities": ["detect", "resolve", "merge_metadata", "keep_existing", "latest"],
        }


__all__ = ["KnowledgeConflictResolver"]

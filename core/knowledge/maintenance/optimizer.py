"""Foundation-08.9 Knowledge optimization routines."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager


class KnowledgeOptimizer:
    """Storage-agnostic optimization/rebuild facade."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()

    def repository_optimize(self) -> Dict[str, Any]:
        items = sorted(self.repository_manager.query(KnowledgeQuery()), key=lambda item: (item.domain, item.key))
        # In-memory repository stores by identity; reinserting normalized order is safe and compatible.
        for item in items:
            self.repository_manager.repository.put(item)
        return {"version": self.version, "optimized": True, "item_count": len(items)}

    def repository_rebuild(self, snapshot: Any = None) -> Dict[str, Any]:
        if snapshot is not None and hasattr(self.repository_manager, "restore"):
            self.repository_manager.restore(snapshot)
        items = self.repository_manager.query(KnowledgeQuery())
        return {"version": self.version, "rebuilt": True, "item_count": len(items)}

    def cache_rebuild(self, cache_manager: Any = None) -> Dict[str, Any]:
        if cache_manager is None:
            return {"version": self.version, "rebuilt": False, "enabled": False}
        if hasattr(cache_manager, "invalidate"):
            cache_manager.invalidate()
        # Warm common domains without changing external behavior.
        warmed = []
        for domain in ["character", "glossary", "narrative", "scene"]:
            if hasattr(cache_manager, "domain_context"):
                cache_manager.domain_context(domain)
                warmed.append(domain)
        return {"version": self.version, "rebuilt": True, "enabled": True, "warmed_domains": warmed}

    def snapshot_compact(self, snapshot_manager: Any = None, keep_latest: int = 5) -> Dict[str, Any]:
        if snapshot_manager is None or not hasattr(snapshot_manager, "list"):
            return {"version": self.version, "compacted": False, "enabled": False}
        names = list(snapshot_manager.list())
        remove = names[:-keep_latest] if keep_latest else names
        removed = 0
        for name in remove:
            if hasattr(snapshot_manager, "registry") and hasattr(snapshot_manager.registry, "_snapshots"):
                snapshot_manager.registry._snapshots.pop(name, None)
                removed += 1
        return {"version": self.version, "compacted": True, "removed_count": removed, "remaining_count": len(names) - removed}


__all__ = ["KnowledgeOptimizer"]

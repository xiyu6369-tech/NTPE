"""Foundation-08.9 Knowledge cleanup routines."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Set, Tuple

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager


class KnowledgeCleanup:
    """Cleanup duplicate, invalid, cache, and snapshot maintenance state."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()

    def repository_cleanup(self, remove_empty_keys: bool = True, remove_duplicate_keys: bool = True) -> Dict[str, Any]:
        items = list(self.repository_manager.query(KnowledgeQuery()))
        seen: Set[Tuple[str, str]] = set()
        removed = 0
        kept = []
        for item in items:
            identity = (item.domain, item.key)
            should_remove = False
            if remove_empty_keys and not item.key:
                should_remove = True
            if remove_duplicate_keys and identity in seen:
                should_remove = True
            if should_remove:
                if self.repository_manager.repository.delete(item.key, item.domain):
                    removed += 1
            else:
                seen.add(identity)
                kept.append(item)
        return {"version": self.version, "removed_count": removed, "remaining_count": len(kept)}

    def cache_cleanup(self, cache_manager: Any = None) -> Dict[str, Any]:
        if cache_manager is None:
            return {"version": self.version, "removed_count": 0, "enabled": False}
        if hasattr(cache_manager, "invalidate"):
            removed = cache_manager.invalidate()
        elif hasattr(cache_manager, "store") and hasattr(cache_manager.store, "clear"):
            removed = cache_manager.store.clear()
        else:
            removed = 0
        return {"version": self.version, "removed_count": removed, "enabled": True}

    def snapshot_cleanup(self, snapshot_manager: Any = None, keep_latest: int = 1) -> Dict[str, Any]:
        if snapshot_manager is None or not hasattr(snapshot_manager, "registry"):
            return {"version": self.version, "removed_count": 0, "enabled": False}
        names = list(snapshot_manager.list()) if hasattr(snapshot_manager, "list") else []
        keep = set(names[-max(keep_latest, 0):]) if keep_latest else set()
        removed = 0
        for name in names:
            if name not in keep:
                # Registry is intentionally simple in 08.7; remove safely if internal map exists.
                if hasattr(snapshot_manager.registry, "_snapshots") and name in snapshot_manager.registry._snapshots:
                    snapshot_manager.registry._snapshots.pop(name, None)
                    removed += 1
        return {"version": self.version, "removed_count": removed, "remaining_count": len(keep), "enabled": True}

    def run_all(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        return {
            "version": self.version,
            "repository": self.repository_cleanup(),
            "cache": self.cache_cleanup(cache_manager),
            "snapshot": self.snapshot_cleanup(snapshot_manager),
        }


__all__ = ["KnowledgeCleanup"]

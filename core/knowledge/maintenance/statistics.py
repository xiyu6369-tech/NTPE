"""Foundation-08.9 Knowledge statistics helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager


class KnowledgeStatistics:
    """Build repository/cache/snapshot metrics for maintenance reports."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()

    def repository_statistics(self) -> Dict[str, Any]:
        items = self.repository_manager.query(KnowledgeQuery())
        domains = Counter(item.domain for item in items)
        keys = Counter((item.domain, item.key) for item in items)
        duplicates = [f"{domain}:{key}" for (domain, key), count in keys.items() if count > 1]
        return {
            "version": self.version,
            "item_count": len(items),
            "domain_count": len(domains),
            "domains": dict(domains),
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
        }

    def cache_statistics(self, cache_manager: Any = None) -> Dict[str, Any]:
        if cache_manager is None:
            return {"version": self.version, "enabled": False}
        if hasattr(cache_manager, "metrics"):
            data = dict(cache_manager.metrics())
        elif hasattr(cache_manager, "store") and hasattr(cache_manager.store, "metrics"):
            data = dict(cache_manager.store.metrics())
        else:
            data = {}
        data.setdefault("version", self.version)
        data["enabled"] = True
        return data

    def snapshot_statistics(self, snapshot_manager: Any = None) -> Dict[str, Any]:
        if snapshot_manager is None:
            return {"version": self.version, "enabled": False, "snapshot_count": 0, "history_count": 0}
        snapshot_names = snapshot_manager.list() if hasattr(snapshot_manager, "list") else []
        history = snapshot_manager.history.list() if hasattr(snapshot_manager, "history") else []
        return {
            "version": self.version,
            "enabled": True,
            "snapshot_count": len(snapshot_names),
            "history_count": len(history),
            "snapshots": list(snapshot_names),
        }

    def report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        return {
            "version": self.version,
            "repository": self.repository_statistics(),
            "cache": self.cache_statistics(cache_manager),
            "snapshot": self.snapshot_statistics(snapshot_manager),
        }


def build_knowledge_statistics(repository_manager: Optional[KnowledgeRepositoryManager] = None) -> KnowledgeStatistics:
    return KnowledgeStatistics(repository_manager=repository_manager)


__all__ = ["KnowledgeStatistics", "build_knowledge_statistics"]

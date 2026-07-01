"""Foundation-08.0 in-memory Knowledge Repository.

The concrete repository is intentionally minimal and dependency-free. It gives
Foundation-08.0 a working contract implementation while future 08.x versions can
add persistence-backed repositories without changing callers.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from .contracts import KnowledgeItem, KnowledgeManifest, KnowledgeQuery, KnowledgeRepository, KnowledgeSnapshot


class InMemoryKnowledgeRepository(KnowledgeRepository):
    """Default runtime-safe repository for Foundation-08.0."""

    version = "foundation-08.0"

    def __init__(self, items: Optional[Iterable[KnowledgeItem]] = None, metadata: Optional[Dict[str, Any]] = None):
        self._items: Dict[Tuple[str, str], KnowledgeItem] = {}
        self.metadata = dict(metadata or {})
        for item in items or []:
            self.put(item)

    def _identity(self, key: str, domain: str = "general") -> Tuple[str, str]:
        return (domain or "general", key)

    def put(self, item: KnowledgeItem) -> KnowledgeItem:
        self._items[self._identity(item.key, item.domain)] = item
        return item

    def put_value(
        self,
        key: str,
        value: Any,
        domain: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> KnowledgeItem:
        item = KnowledgeItem(key=key, value=value, domain=domain, metadata=dict(metadata or {}), source=source)
        return self.put(item)

    def get(self, key: str, domain: str = "general") -> Optional[KnowledgeItem]:
        return self._items.get(self._identity(key, domain))

    def query(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        results = [item for item in self._items.values() if query.matches(item)]
        results.sort(key=lambda item: (item.domain, item.key))
        if query.limit is not None:
            return results[: int(query.limit)]
        return results

    def delete(self, key: str, domain: str = "general") -> bool:
        return self._items.pop(self._identity(key, domain), None) is not None

    def snapshot(self, name: str = "default") -> KnowledgeSnapshot:
        return KnowledgeSnapshot(
            name=name,
            items=list(self.query(KnowledgeQuery())),
            metadata={"repository": self.__class__.__name__, **self.metadata},
        )

    def load_snapshot(self, snapshot: KnowledgeSnapshot | Dict[str, Any]) -> "InMemoryKnowledgeRepository":
        if isinstance(snapshot, dict):
            snapshot = KnowledgeSnapshot.from_dict(snapshot)
        self._items.clear()
        for item in snapshot.items:
            self.put(item)
        return self

    def manifest(self) -> KnowledgeManifest:
        return KnowledgeManifest(
            name="in_memory_knowledge_repository",
            metadata={
                "item_count": len(self._items),
                "storage": "memory",
                **self.metadata,
            },
        )


def build_repository_from_intelligence_snapshot(snapshot: Optional[Dict[str, Any]]) -> InMemoryKnowledgeRepository:
    """Build a Knowledge Repository from a Foundation-07 intelligence snapshot.

    This adapter is intentionally tolerant of missing keys because older
    Foundation-07 callers may attach partial snapshots.
    """

    repository = InMemoryKnowledgeRepository(metadata={"source": "intelligence_snapshot"})
    snapshot = snapshot or {}

    for key, value in dict(snapshot.get("characters") or {}).items():
        repository.put_value(str(key), value, domain="character", source="intelligence")

    for key, value in dict(snapshot.get("glossary") or {}).items():
        repository.put_value(str(key), value, domain="glossary", source="intelligence")

    narrative = snapshot.get("narrative") or []
    if isinstance(narrative, dict):
        iterable = narrative.items()
    else:
        iterable = enumerate(narrative)
    for key, value in iterable:
        repository.put_value(str(key), value, domain="narrative", source="intelligence")

    scenes = snapshot.get("scenes") or []
    if isinstance(scenes, dict):
        scene_iterable = scenes.items()
    else:
        scene_iterable = enumerate(scenes)
    for key, value in scene_iterable:
        repository.put_value(str(key), value, domain="scene", source="intelligence")

    return repository


__all__ = ["InMemoryKnowledgeRepository", "build_repository_from_intelligence_snapshot"]

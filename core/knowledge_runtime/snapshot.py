"""RM-6.1.1 Snapshot — serialize, hierarchize, and restore runtime state.

No provider imports. Pure local snapshotting on KnowledgeSnapshot datamodels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .errors import KnowledgeSnapshotError
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgeSnapshot


class KnowledgeSnapshotStore:
    """Store, retrieve, diff, and merge KnowledgeSnapshot instances.

    All operations are local. No external persistence or provider
    coupling. This is an offline runtime component.
    """

    version = "rm-6.1.1"

    def __init__(self):
        self._snapshots: Dict[str, KnowledgeSnapshot] = {}

    def store(self, snapshot: KnowledgeSnapshot) -> KnowledgeSnapshot:
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    def retrieve(self, snapshot_id: str) -> KnowledgeSnapshot:
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise KnowledgeSnapshotError(f"Snapshot not found: {snapshot_id}")
        return snapshot

    def list_ids(self) -> List[str]:
        return sorted(self._snapshots.keys())

    def delete(self, snapshot_id: str) -> bool:
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            return True
        return False

    def build(
        self,
        snapshot_id: str,
        bundles: Optional[List[KnowledgeBundle]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeSnapshot:
        snapshot = KnowledgeSnapshot(
            id=snapshot_id,
            bundles=bundles or [],
            metadata=dict(metadata or {}),
        )
        return self.store(snapshot)

    def restore_bundles(self, snapshot_id: str) -> List[KnowledgeBundle]:
        snapshot = self.retrieve(snapshot_id)
        return list(snapshot.bundles)

    def restore_entries(self, snapshot_id: str) -> List[KnowledgeEntry]:
        bundles = self.restore_bundles(snapshot_id)
        entries: List[KnowledgeEntry] = []
        for bundle in bundles:
            entries.extend(bundle.entries)
        return entries

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_snapshot_store",
            "version": self.version,
            "stored_snapshot_ids": self.list_ids(),
            "enabled": True,
        }


class SnapshotHierarchy:
    """Novel → Volume → Chapter → Chunk layered knowledge hierarchy.

    Higher levels provide defaults. Lower levels override higher levels.
    No merge conflicts. No persistence. Pure immutable layered resolution.
    """

    class Level:
        NOVEL = "novel"
        VOLUME = "volume"
        CHAPTER = "chapter"
        CHUNK = "chunk"

    ORDER = [Level.NOVEL, Level.VOLUME, Level.CHAPTER, Level.CHUNK]

    def __init__(self):
        self._layers: Dict[str, Dict[str, Dict[str, Any]]] = {
            level: {} for level in self.ORDER
        }

    def set_layer(
        self,
        level: str,
        domain: str,
        entries: Dict[str, Any],
    ) -> None:
        if level not in self._layers:
            raise KnowledgeSnapshotError(f"Unknown hierarchy level: {level}")
        self._layers[level][domain] = dict(entries)

    def set_novel(self, domain: str, entries: Dict[str, Any]) -> None:
        self.set_layer(self.Level.NOVEL, domain, entries)

    def set_volume(self, domain: str, entries: Dict[str, Any]) -> None:
        self.set_layer(self.Level.VOLUME, domain, entries)

    def set_chapter(self, domain: str, entries: Dict[str, Any]) -> None:
        self.set_layer(self.Level.CHAPTER, domain, entries)

    def set_chunk(self, domain: str, entries: Dict[str, Any]) -> None:
        self.set_layer(self.Level.CHUNK, domain, entries)

    def resolve(self, key: str, domain: str = "general") -> Any:
        """Resolve a key through the hierarchy from Chunk → Novel (top-down).

        Lower levels override higher levels. Returns None if not found.
        """
        for level in reversed(self.ORDER):
            layer = self._layers[level]
            domain_entries = layer.get(domain, {})
            if key in domain_entries:
                return domain_entries[key]
        return None

    def resolve_all(self, domain: str) -> Dict[str, Any]:
        """Resolve all keys for a domain through the hierarchy.

        Novel defaults come first, then overlays from Volume down
        to Chunk. Lower levels replace higher-level values for the
        same key — no merge conflicts.
        """
        merged: Dict[str, Any] = {}
        for level in self.ORDER:
            layer = self._layers[level]
            domain_entries = layer.get(domain, {})
            merged.update(domain_entries)
        return merged

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "snapshot_hierarchy",
            "version": "rm-6.1.1",
            "levels": self.ORDER,
            "populated_layers": {
                level: list(self._layers[level].keys())
                for level in self.ORDER
            },
        }


__all__ = ["KnowledgeSnapshotStore", "SnapshotHierarchy"]
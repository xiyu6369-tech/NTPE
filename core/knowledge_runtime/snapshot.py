"""RM-6.1.0 Snapshot — serialize and restore runtime state.

No provider imports. Pure local snapshotting on KnowledgeSnapshot datamodels.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .errors import KnowledgeSnapshotError
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgeSnapshot


class KnowledgeSnapshotStore:
    """Store, retrieve, diff, and merge KnowledgeSnapshot instances.

    All operations are local. No external persistence or provider
    coupling. This is an offline runtime component.
    """

    version = "rm-6.1.0"

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

    def build(self, snapshot_id: str, bundles: Optional[List[KnowledgeBundle]] = None, metadata: Optional[Dict[str, Any]] = None) -> KnowledgeSnapshot:
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


__all__ = ["KnowledgeSnapshotStore"]
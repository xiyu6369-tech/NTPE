"""Foundation-08.7 Knowledge Snapshot registry."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..contracts import KnowledgeSnapshot


class KnowledgeSnapshotRegistry:
    """Named in-memory registry for versioned knowledge snapshots."""

    version = "foundation-08.7"

    def __init__(self):
        self._snapshots: Dict[str, KnowledgeSnapshot] = {}
        self._latest: Optional[str] = None

    def register(self, snapshot: KnowledgeSnapshot, name: Optional[str] = None) -> KnowledgeSnapshot:
        key = name or snapshot.name or "default"
        self._snapshots[key] = snapshot
        self._latest = key
        return snapshot

    def get(self, name: Optional[str] = None) -> Optional[KnowledgeSnapshot]:
        if name is None:
            name = self._latest
        if name is None:
            return None
        return self._snapshots.get(name)

    def delete(self, name: str) -> bool:
        removed = self._snapshots.pop(name, None) is not None
        if self._latest == name:
            self._latest = next(reversed(self._snapshots), None) if self._snapshots else None
        return removed

    def list(self) -> List[str]:
        return list(self._snapshots.keys())

    def clear(self) -> None:
        self._snapshots.clear()
        self._latest = None

    def manifest(self) -> Dict[str, object]:
        return {
            "name": "knowledge_snapshot_registry",
            "version": self.version,
            "enabled": True,
            "capabilities": ["register", "get", "delete", "list", "latest"],
            "metadata": {"snapshot_count": len(self._snapshots), "latest": self._latest},
        }


__all__ = ["KnowledgeSnapshotRegistry"]

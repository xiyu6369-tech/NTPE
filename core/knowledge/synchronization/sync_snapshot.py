"""Foundation-08.3 snapshot synchronization helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeSnapshot, utc_now_iso


class KnowledgeSyncSnapshot:
    """Wrap and version synchronization snapshots."""

    version = "foundation-08.3"

    def __init__(self, snapshot: KnowledgeSnapshot, sync_id: str = "default", metadata: Optional[Dict[str, Any]] = None):
        self.snapshot = snapshot
        self.sync_id = sync_id
        self.metadata = dict(metadata or {})
        self.created_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "knowledge_sync_snapshot",
            "version": self.version,
            "sync_id": self.sync_id,
            "snapshot": self.snapshot.to_dict(),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeSyncSnapshot":
        return cls(
            snapshot=KnowledgeSnapshot.from_dict(payload.get("snapshot", {})),
            sync_id=str(payload.get("sync_id", "default")),
            metadata=dict(payload.get("metadata") or {}),
        )


def build_sync_snapshot(snapshot: KnowledgeSnapshot, sync_id: str = "default", **metadata: Any) -> KnowledgeSyncSnapshot:
    return KnowledgeSyncSnapshot(snapshot=snapshot, sync_id=sync_id, metadata=metadata)


__all__ = ["KnowledgeSyncSnapshot", "build_sync_snapshot"]

"""Foundation-08.7 Knowledge Snapshot history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..contracts import KnowledgeSnapshot, utc_now_iso


@dataclass
class KnowledgeSnapshotHistoryEntry:
    """Single snapshot history entry."""

    snapshot: KnowledgeSnapshot
    revision: int
    created_at: str = field(default_factory=utc_now_iso)
    label: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "revision": self.revision,
            "created_at": self.created_at,
            "label": self.label,
            "snapshot": self.snapshot.to_dict(),
        }


class KnowledgeSnapshotHistory:
    """Append-only snapshot history for rollback and audit use cases."""

    version = "foundation-08.7"

    def __init__(self):
        self._entries: List[KnowledgeSnapshotHistoryEntry] = []

    def add(self, snapshot: KnowledgeSnapshot, label: str = "") -> KnowledgeSnapshotHistoryEntry:
        entry = KnowledgeSnapshotHistoryEntry(snapshot=snapshot, revision=len(self._entries) + 1, label=label)
        self._entries.append(entry)
        return entry

    def latest(self) -> Optional[KnowledgeSnapshotHistoryEntry]:
        return self._entries[-1] if self._entries else None

    def get(self, revision: int) -> Optional[KnowledgeSnapshotHistoryEntry]:
        if revision <= 0:
            return None
        for entry in self._entries:
            if entry.revision == revision:
                return entry
        return None

    def list(self) -> List[KnowledgeSnapshotHistoryEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def to_dict(self) -> Dict[str, object]:
        return {"version": self.version, "entries": [entry.to_dict() for entry in self._entries]}


__all__ = ["KnowledgeSnapshotHistory", "KnowledgeSnapshotHistoryEntry"]

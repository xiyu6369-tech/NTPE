"""Foundation-08.7 Knowledge Snapshot diff and merge helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from ..contracts import KnowledgeItem, KnowledgeSnapshot


Identity = Tuple[str, str]


def _index(snapshot: KnowledgeSnapshot) -> Dict[Identity, KnowledgeItem]:
    return {(item.domain, item.key): item for item in snapshot.items}


@dataclass
class KnowledgeSnapshotDiff:
    """Portable snapshot difference result."""

    added: List[KnowledgeItem] = field(default_factory=list)
    removed: List[KnowledgeItem] = field(default_factory=list)
    changed: List[KnowledgeItem] = field(default_factory=list)
    unchanged: List[KnowledgeItem] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def to_dict(self) -> Dict[str, object]:
        return {
            "added": [item.to_dict() for item in self.added],
            "removed": [item.to_dict() for item in self.removed],
            "changed": [item.to_dict() for item in self.changed],
            "unchanged": [item.to_dict() for item in self.unchanged],
            "change_count": len(self.added) + len(self.removed) + len(self.changed),
        }


class KnowledgeSnapshotDiffer:
    """Compute deterministic diffs between two knowledge snapshots."""

    version = "foundation-08.7"

    def diff(self, before: KnowledgeSnapshot, after: KnowledgeSnapshot) -> KnowledgeSnapshotDiff:
        before_items = _index(before)
        after_items = _index(after)
        added: List[KnowledgeItem] = []
        removed: List[KnowledgeItem] = []
        changed: List[KnowledgeItem] = []
        unchanged: List[KnowledgeItem] = []

        for identity, item in after_items.items():
            old = before_items.get(identity)
            if old is None:
                added.append(item)
            elif old.to_dict() != item.to_dict():
                changed.append(item)
            else:
                unchanged.append(item)

        for identity, item in before_items.items():
            if identity not in after_items:
                removed.append(item)

        key = lambda item: (item.domain, item.key)
        return KnowledgeSnapshotDiff(
            added=sorted(added, key=key),
            removed=sorted(removed, key=key),
            changed=sorted(changed, key=key),
            unchanged=sorted(unchanged, key=key),
        )


def merge_snapshots(name: str, snapshots: Iterable[KnowledgeSnapshot], prefer: str = "latest") -> KnowledgeSnapshot:
    """Merge snapshots into one portable KnowledgeSnapshot.

    prefer="latest" means later snapshots override earlier snapshots.
    prefer="first" keeps the first item found for each domain/key.
    """

    merged: Dict[Identity, KnowledgeItem] = {}
    source_names: List[str] = []
    for snapshot in snapshots:
        source_names.append(snapshot.name)
        for item in snapshot.items:
            identity = (item.domain, item.key)
            if prefer == "first" and identity in merged:
                continue
            merged[identity] = item
    return KnowledgeSnapshot(
        name=name,
        version="foundation-08.7",
        items=sorted(merged.values(), key=lambda item: (item.domain, item.key)),
        metadata={"merged": True, "source_snapshots": source_names, "prefer": prefer},
    )


__all__ = ["KnowledgeSnapshotDiff", "KnowledgeSnapshotDiffer", "merge_snapshots"]

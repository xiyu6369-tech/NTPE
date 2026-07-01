"""Foundation-08.7 Knowledge Snapshot Manager."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..contracts import KnowledgeItem, KnowledgeRepository, KnowledgeSnapshot
from ..repository import InMemoryKnowledgeRepository
from .manifest import build_knowledge_snapshot_manifest
from .snapshot_diff import KnowledgeSnapshotDiff, KnowledgeSnapshotDiffer, merge_snapshots
from .snapshot_history import KnowledgeSnapshotHistory
from .snapshot_registry import KnowledgeSnapshotRegistry
from .snapshot_serializer import KnowledgeSnapshotSerializer


class KnowledgeSnapshotManager:
    """Centralized snapshot manager for Knowledge Layer repositories.

    This manager does not replace existing repository/runtime snapshot methods;
    it wraps them to provide version history, diff, merge, rollback, import, and
    export without breaking Foundation-08.0 through 08.6 callers.
    """

    version = "foundation-08.7"

    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        registry: Optional[KnowledgeSnapshotRegistry] = None,
        history: Optional[KnowledgeSnapshotHistory] = None,
        serializer: Optional[KnowledgeSnapshotSerializer] = None,
        differ: Optional[KnowledgeSnapshotDiffer] = None,
        event_bus: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.repository = repository or InMemoryKnowledgeRepository(metadata={"source": "snapshot_manager"})
        self.registry = registry or KnowledgeSnapshotRegistry()
        self.history = history or KnowledgeSnapshotHistory()
        self.serializer = serializer or KnowledgeSnapshotSerializer()
        self.differ = differ or KnowledgeSnapshotDiffer()
        self.event_bus = event_bus
        self.metadata = dict(metadata or {})

    def _publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.event_bus is None:
            return
        data = {"event_type": event_type, "payload": dict(payload or {})}
        # Foundation-07 Event Bus versions used publish(event) or publish(type, payload).
        try:
            self.event_bus.publish(event_type, dict(payload or {}))
        except TypeError:
            try:
                self.event_bus.publish(data)
            except Exception:
                pass
        except Exception:
            pass

    def create(self, name: str = "default", label: str = "", repository: Optional[KnowledgeRepository] = None) -> KnowledgeSnapshot:
        repo = repository or self.repository
        snapshot = repo.snapshot(name=name)
        snapshot.version = self.version
        snapshot.metadata.update({"manager": self.version, **self.metadata})
        self.registry.register(snapshot, name=name)
        self.history.add(snapshot, label=label or name)
        self._publish("KnowledgeSnapshotCreated", {"name": snapshot.name, "item_count": len(snapshot.items)})
        return snapshot

    def register(self, snapshot: KnowledgeSnapshot | Dict[str, Any], name: Optional[str] = None, label: str = "") -> KnowledgeSnapshot:
        snap = self.serializer.from_dict(snapshot) if isinstance(snapshot, dict) else snapshot
        self.registry.register(snap, name=name or snap.name)
        self.history.add(snap, label=label or name or snap.name)
        self._publish("KnowledgeSnapshotRegistered", {"name": name or snap.name, "item_count": len(snap.items)})
        return snap

    def get(self, name: Optional[str] = None) -> Optional[KnowledgeSnapshot]:
        return self.registry.get(name)

    def list(self) -> list[str]:
        return self.registry.list()

    def diff(self, before: KnowledgeSnapshot | str, after: KnowledgeSnapshot | str) -> KnowledgeSnapshotDiff:
        left = self.registry.get(before) if isinstance(before, str) else before
        right = self.registry.get(after) if isinstance(after, str) else after
        if left is None or right is None:
            raise KeyError("Snapshot not found for diff")
        result = self.differ.diff(left, right)
        self._publish("KnowledgeSnapshotDiffed", result.to_dict())
        return result

    def merge(self, name: str, snapshots: Iterable[KnowledgeSnapshot | str], prefer: str = "latest", label: str = "merged") -> KnowledgeSnapshot:
        resolved = []
        for snapshot in snapshots:
            resolved_snapshot = self.registry.get(snapshot) if isinstance(snapshot, str) else snapshot
            if resolved_snapshot is None:
                raise KeyError("Snapshot not found for merge")
            resolved.append(resolved_snapshot)
        merged = merge_snapshots(name=name, snapshots=resolved, prefer=prefer)
        return self.register(merged, name=name, label=label)

    def rollback(self, revision: Optional[int] = None, name: Optional[str] = None, repository: Optional[InMemoryKnowledgeRepository] = None) -> KnowledgeSnapshot:
        if name is not None:
            snapshot = self.registry.get(name)
        elif revision is not None:
            entry = self.history.get(revision)
            snapshot = entry.snapshot if entry else None
        else:
            latest = self.history.latest()
            snapshot = latest.snapshot if latest else self.registry.get()
        if snapshot is None:
            raise KeyError("Snapshot not found for rollback")

        target = repository or self.repository
        if hasattr(target, "load_snapshot"):
            target.load_snapshot(snapshot)  # type: ignore[attr-defined]
        else:
            # Contract-safe fallback for custom repositories.
            existing = target.snapshot(name="before_rollback")
            for item in existing.items:
                target.delete(item.key, item.domain)
            for item in snapshot.items:
                target.put(item)
        self._publish("KnowledgeSnapshotRolledBack", {"name": snapshot.name, "revision": revision})
        return snapshot

    def export(self, snapshot: KnowledgeSnapshot | str, path: str | Path) -> Path:
        snap = self.registry.get(snapshot) if isinstance(snapshot, str) else snapshot
        if snap is None:
            raise KeyError("Snapshot not found for export")
        output = self.serializer.save(snap, path)
        self._publish("KnowledgeSnapshotExported", {"name": snap.name, "path": str(output)})
        return output

    def import_snapshot(self, path: str | Path, name: Optional[str] = None, label: str = "imported") -> KnowledgeSnapshot:
        snapshot = self.serializer.load(path)
        if name:
            snapshot.name = name
        self.register(snapshot, name=snapshot.name, label=label)
        self._publish("KnowledgeSnapshotImported", {"name": snapshot.name, "path": str(path)})
        return snapshot

    def snapshot_runtime_payload(self, name: str = "runtime") -> Dict[str, Any]:
        snapshot = self.create(name=name)
        return {
            "knowledge_snapshot": snapshot.to_dict(),
            "knowledge_snapshot_manifest": self.manifest(),
        }

    def attach_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None, name: str = "runtime") -> Dict[str, Any]:
        payload = dict(manifest or {})
        snapshot = self.create(name=name)
        payload["knowledge_snapshot"] = snapshot.to_dict()
        payload["knowledge_snapshot_manager"] = self.manifest()
        return payload

    def manifest(self) -> Dict[str, Any]:
        return build_knowledge_snapshot_manifest(
            snapshot_count=len(self.registry.list()),
            history_count=len(self.history.list()),
            **self.metadata,
        )


def build_snapshot_manager(repository: Optional[KnowledgeRepository] = None, **metadata: Any) -> KnowledgeSnapshotManager:
    return KnowledgeSnapshotManager(repository=repository, metadata=metadata)


__all__ = ["KnowledgeSnapshotManager", "build_snapshot_manager"]

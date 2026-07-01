"""Foundation-08.3 Knowledge Synchronization Manager."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery, KnowledgeSnapshot
from ..repositories.manager import KnowledgeRepositoryManager
from ..runtime.runtime import KnowledgeRuntime
from .conflict_resolver import KnowledgeConflictResolver
from .manifest import build_knowledge_synchronization_manifest
from .sync_context import KnowledgeSyncContext, build_sync_context
from .sync_runtime import KnowledgeSyncRuntime
from .sync_snapshot import KnowledgeSyncSnapshot, build_sync_snapshot


class KnowledgeSynchronizationManager:
    """Coordinate Repository, Runtime, Snapshot, and Event Bus synchronization."""

    version = "foundation-08.3"

    def __init__(
        self,
        repository_manager: Optional[KnowledgeRepositoryManager] = None,
        runtime: Optional[KnowledgeRuntime] = None,
        event_bus: Any = None,
        conflict_resolver: Optional[KnowledgeConflictResolver] = None,
    ):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()
        self.runtime = runtime or KnowledgeRuntime(manager=self.repository_manager, event_bus=event_bus)
        self.runtime_sync = KnowledgeSyncRuntime(self.runtime)
        self.event_bus = event_bus
        self.conflict_resolver = conflict_resolver or KnowledgeConflictResolver()
        self.history: List[Dict[str, Any]] = []

    def _publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.event_bus is None:
            return
        data = {"version": self.version, **dict(payload or {})}
        if hasattr(self.event_bus, "publish"):
            try:
                self.event_bus.publish(event_type, data)
            except TypeError:
                self.event_bus.publish({"event_type": event_type, "payload": data})

    def build_context(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, **metadata: Any) -> KnowledgeSyncContext:
        context = build_sync_context(segment=segment, payload=payload, **metadata)
        self._publish("KnowledgeSyncContextCreated", {"segment_id": context.segment_id, "session_id": context.session_id})
        return context

    def sync_repository(self, items: Iterable[KnowledgeItem | Dict[str, Any]], context: Optional[KnowledgeSyncContext] = None) -> Dict[str, Any]:
        context = context or KnowledgeSyncContext()
        updated: List[KnowledgeItem] = []
        conflicts: List[Dict[str, Any]] = []
        for raw in items:
            incoming = raw if isinstance(raw, KnowledgeItem) else KnowledgeItem.from_dict(raw)
            current = self.repository_manager.get(incoming.key, incoming.domain)
            if self.conflict_resolver.has_conflict(current, incoming):
                conflicts.append({"key": incoming.key, "domain": incoming.domain})
            resolved = self.conflict_resolver.resolve(current, incoming)
            updated.append(self.repository_manager.repository.put(resolved))
            context.add_item(resolved)
        result = {
            "type": "knowledge_repository_sync_result",
            "version": self.version,
            "updated_count": len(updated),
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "items": [item.to_dict() for item in updated],
            "context": context.to_dict(),
        }
        self.history.append(result)
        self._publish("KnowledgeRepositorySynced", result)
        return result

    def sync_runtime(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = self.build_context(segment=segment, payload=payload)
        before = self.runtime_sync.pull_runtime_context(segment=segment, payload=payload)
        incoming_items = []
        for item in (result or {}).get("knowledge_items", []):
            incoming_items.append(KnowledgeItem.from_dict(item))
        repo_result = self.sync_repository(incoming_items, context=context) if incoming_items else {
            "updated_count": 0,
            "conflict_count": 0,
            "items": [],
            "context": context.to_dict(),
        }
        checkpoint = self.runtime_sync.checkpoint(context)
        output = {
            "type": "knowledge_runtime_sync_result",
            "version": self.version,
            "before": before,
            "repository": repo_result,
            "checkpoint": checkpoint,
        }
        self._publish("KnowledgeRuntimeSynced", {"segment_id": context.segment_id, "updated_count": repo_result.get("updated_count", 0)})
        return output

    def sync_snapshot(self, name: str = "sync", context: Optional[KnowledgeSyncContext] = None) -> KnowledgeSyncSnapshot:
        snapshot: KnowledgeSnapshot = self.repository_manager.snapshot(name)
        sync_snapshot = build_sync_snapshot(snapshot, sync_id=name, context=(context.to_dict() if context else {}))
        self._publish("KnowledgeSnapshotSynced", {"name": name, "item_count": len(snapshot.items)})
        return sync_snapshot

    def process(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime_result = self.sync_runtime(segment=segment, payload=payload, result=result)
        sync_snapshot = self.sync_snapshot("process")
        return {
            "type": "knowledge_synchronization_payload",
            "version": self.version,
            "runtime": runtime_result,
            "snapshot": sync_snapshot.to_dict(),
            "manifest": self.manifest(),
        }

    def query(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        return self.repository_manager.query(query)

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = build_knowledge_synchronization_manifest(metadata)
        manifest["conflict_resolver"] = self.conflict_resolver.manifest()
        manifest["repository"] = self.repository_manager.repository.manifest().to_dict()
        return manifest

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


__all__ = ["KnowledgeSynchronizationManager"]

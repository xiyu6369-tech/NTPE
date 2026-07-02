"""Persistence manager for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
from typing import Any, Dict
from .persistence_models import WORKFLOW_PERSISTENCE_STAGE, WORKFLOW_PERSISTENCE_VERSION, PersistenceResult, PersistenceStatus, SnapshotKind, WorkflowSnapshot
from .persistence_store import PersistenceStore
from .state_serializer import StateSerializer
from .state_deserializer import StateDeserializer
from .checkpoint_manager import CheckpointManager
from .recovery_manager import RecoveryManager
from .persistence_events import PERSISTENCE_EVENTS

class PersistenceManager:
    version = WORKFLOW_PERSISTENCE_VERSION
    stage = WORKFLOW_PERSISTENCE_STAGE

    def __init__(self, *, store: PersistenceStore | None = None, event_bus: Any = None, metadata: Dict[str, Any] | None = None) -> None:
        self.store = store or PersistenceStore()
        self.event_bus = event_bus
        self.metadata = dict(metadata or {})
        self.serializer = StateSerializer()
        self.deserializer = StateDeserializer()
        self.checkpoints = CheckpointManager()
        self.recovery = RecoveryManager()
        self.snapshots: Dict[str, WorkflowSnapshot] = {}

    def _publish(self, key: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(PERSISTENCE_EVENTS[key], payload, topic="workflow.persistence", source="persistence_manager")

    def create_snapshot(self, name: str, *, kind: SnapshotKind | str = SnapshotKind.WORKFLOW, state: Dict[str, Any] | None = None, metadata: Dict[str, Any] | None = None) -> WorkflowSnapshot:
        snapshot = WorkflowSnapshot(name=name, kind=kind, state=dict(state or {}), metadata={**self.metadata, **dict(metadata or {})})
        self.snapshots[snapshot.snapshot_id] = snapshot
        self._publish("snapshot_created", {"snapshot_id": snapshot.snapshot_id, "name": name, "kind": snapshot.kind.value})
        return snapshot

    def save_snapshot(self, snapshot: WorkflowSnapshot) -> PersistenceResult:
        self.snapshots[snapshot.snapshot_id] = snapshot
        self.store.save(snapshot.snapshot_id, self.serializer.dumps(snapshot.to_dict()))
        self._publish("state_saved", {"snapshot_id": snapshot.snapshot_id})
        return PersistenceResult(ok=True, status=PersistenceStatus.SAVED, snapshot=snapshot)

    def load_snapshot(self, snapshot_id: str) -> WorkflowSnapshot:
        if snapshot_id in self.snapshots:
            snapshot = self.snapshots[snapshot_id]
        else:
            snapshot = WorkflowSnapshot.from_dict(self.deserializer.loads(self.store.load(snapshot_id)))
            self.snapshots[snapshot.snapshot_id] = snapshot
        self._publish("state_loaded", {"snapshot_id": snapshot.snapshot_id})
        return snapshot

    def create_checkpoint(self, name: str, snapshot: WorkflowSnapshot, **metadata: Any) -> PersistenceResult:
        checkpoint = self.checkpoints.create(name, snapshot, **metadata)
        self._publish("checkpoint_created", {"checkpoint_id": checkpoint.checkpoint_id, "snapshot_id": snapshot.snapshot_id})
        return PersistenceResult(ok=True, status=PersistenceStatus.SAVED, snapshot=snapshot, checkpoint=checkpoint)

    def recover(self, snapshot_id: str, target: Any | None = None) -> PersistenceResult:
        snapshot = self.load_snapshot(snapshot_id)
        result = self.recovery.recover(snapshot, target=target)
        self._publish("workflow_recovered", {"snapshot_id": snapshot.snapshot_id})
        return result

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "job_scheduler_compatible": True,
            "pipeline_orchestrator_compatible": True,
            "task_queue_compatible": True,
            "worker_runtime_compatible": True,
            "additive_only": True,
            "snapshots": len(self.snapshots),
            "checkpoints": len(list(self.checkpoints.all())),
            "metadata": dict(self.metadata),
        }

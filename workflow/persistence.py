"""Public Workflow Persistence API for NTPE 1.0 Beta Stage-09.5."""
from __future__ import annotations
from typing import Any, Dict

from .persistence_manager import PersistenceManager
from .persistence_store import PersistenceStore
from .persistence_models import WORKFLOW_PERSISTENCE_STAGE, WORKFLOW_PERSISTENCE_VERSION, SnapshotKind

class WorkflowPersistence:
    version = WORKFLOW_PERSISTENCE_VERSION
    stage = WORKFLOW_PERSISTENCE_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None, task_queue: Any = None, worker_runtime: Any = None, store: PersistenceStore | None = None, metadata: Dict[str, Any] | None = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator
        self.task_queue = task_queue
        self.worker_runtime = worker_runtime
        self.metadata = dict(metadata or {})
        self.manager = PersistenceManager(store=store, event_bus=event_bus, metadata=self.metadata)

    def snapshot_workflow(self, name: str, *, state: Dict[str, Any] | None = None, **metadata: Any):
        snapshot = self.manager.create_snapshot(name, kind=SnapshotKind.WORKFLOW, state=state or self._collect_state(), metadata=metadata)
        return self.manager.save_snapshot(snapshot)

    def checkpoint(self, name: str, snapshot=None, **metadata: Any):
        if snapshot is None:
            snapshot = self.manager.create_snapshot(name, kind=SnapshotKind.CHECKPOINT, state=self._collect_state(), metadata=metadata)
            self.manager.save_snapshot(snapshot)
        return self.manager.create_checkpoint(name, snapshot, **metadata)

    def load(self, snapshot_id: str):
        return self.manager.load_snapshot(snapshot_id)

    def resume(self, snapshot_id: str, target: Any | None = None):
        return self.manager.recover(snapshot_id, target=target)

    def _collect_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for key, obj in {
            "workflow_core": self.workflow_core,
            "job_scheduler": self.job_scheduler,
            "pipeline_orchestrator": self.pipeline_orchestrator,
            "task_queue": self.task_queue,
            "worker_runtime": self.worker_runtime,
        }.items():
            if obj is not None:
                if hasattr(obj, "manifest"):
                    state[key] = obj.manifest()
                elif hasattr(obj, "to_dict"):
                    state[key] = obj.to_dict()
                else:
                    state[key] = repr(obj)
        return state

    def manifest(self) -> dict:
        manifest = self.manager.manifest()
        manifest["bridges"] = {
            "event_bus_attached": self.event_bus is not None,
            "service_container_attached": self.service_container is not None,
            "workflow_core_attached": self.workflow_core is not None,
            "job_scheduler_attached": self.job_scheduler is not None,
            "pipeline_orchestrator_attached": self.pipeline_orchestrator is not None,
            "task_queue_attached": self.task_queue is not None,
            "worker_runtime_attached": self.worker_runtime is not None,
        }
        return manifest

def create_workflow_persistence(**kwargs: Any) -> WorkflowPersistence:
    return WorkflowPersistence(**kwargs)

from __future__ import annotations
from typing import Any
from .models import DISTRIBUTED_EXECUTION_STAGE, DISTRIBUTED_EXECUTION_VERSION, DistributionStrategy
from .node_registry import NodeRegistry
from .scheduler import DistributedScheduler
from .dispatcher import DistributedDispatcher
from .heartbeat import HeartbeatMonitor
from .failover import FailoverManager
from .topology import TopologyManager

class DistributedCoordinator:
    version = DISTRIBUTED_EXECUTION_VERSION
    stage = DISTRIBUTED_EXECUTION_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None, task_queue: Any = None, worker_runtime: Any = None, persistence: Any = None, strategy: DistributionStrategy | str = DistributionStrategy.LEAST_LOADED, metadata: dict | None = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator
        self.task_queue = task_queue
        self.worker_runtime = worker_runtime
        self.persistence = persistence
        self.metadata = dict(metadata or {})
        self.registry = NodeRegistry()
        self.scheduler = DistributedScheduler(self.registry, strategy=strategy)
        self.dispatcher = DistributedDispatcher(self.scheduler, event_bus=event_bus, worker_runtime=worker_runtime)
        self.heartbeat = HeartbeatMonitor(self.registry, event_bus=event_bus)
        self.failover_manager = FailoverManager(self.registry, self.dispatcher, event_bus=event_bus)
        self.topology = TopologyManager(self.registry)
        self.running = False

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.distributed", source="distributed_coordinator")

    def start(self) -> "DistributedCoordinator":
        self.running = True
        self._publish("distributed.coordinator.started", {"stage": self.stage})
        return self

    def stop(self) -> "DistributedCoordinator":
        self.running = False
        self._publish("distributed.coordinator.stopped", {"stage": self.stage})
        return self

    def register_node(self, name: str, capacity: int = 1, **metadata):
        node = self.registry.create(name, capacity=capacity, **metadata)
        self._publish("distributed.node.registered", {"node_id": node.node_id, "name": name, "capacity": capacity})
        return node

    def distribute_task(self, task: Any):
        if not self.running:
            self.start()
        return self.dispatcher.dispatch(task)

    def beat(self, node_id: str):
        return self.heartbeat.beat(node_id)

    def failover(self, failed_node_id: str, task: Any):
        return self.failover_manager.failover(failed_node_id, task)

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "running": self.running,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "job_scheduler_compatible": True,
            "pipeline_orchestrator_compatible": True,
            "task_queue_compatible": True,
            "worker_runtime_compatible": True,
            "persistence_compatible": True,
            "additive_only": True,
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
                "workflow_core_attached": self.workflow_core is not None,
                "job_scheduler_attached": self.job_scheduler is not None,
                "pipeline_orchestrator_attached": self.pipeline_orchestrator is not None,
                "task_queue_attached": self.task_queue is not None,
                "worker_runtime_attached": self.worker_runtime is not None,
                "persistence_attached": self.persistence is not None,
            },
            "nodes": self.registry.manifest(),
            "topology": self.topology.build().to_dict(),
            "metadata": dict(self.metadata),
        }

def create_distributed_coordinator(**kwargs: Any) -> DistributedCoordinator:
    return DistributedCoordinator(**kwargs)

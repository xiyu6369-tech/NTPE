from __future__ import annotations
from typing import Any
from .node_registry import NodeRegistry
from .dispatcher import DistributedDispatcher

class FailoverManager:
    def __init__(self, registry: NodeRegistry, dispatcher: DistributedDispatcher, event_bus=None) -> None:
        self.registry = registry
        self.dispatcher = dispatcher
        self.event_bus = event_bus

    def failover(self, failed_node_id: str, task: Any):
        self.registry.mark_failed(failed_node_id, "failover_requested")
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish("distributed.failover", {"failed_node_id": failed_node_id, "task_id": getattr(task, "task_id", None)}, topic="workflow.distributed", source="failover")
        return self.dispatcher.dispatch(task)

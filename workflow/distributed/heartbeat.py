from __future__ import annotations
import time
from .node_registry import NodeRegistry
from .models import NodeStatus

class HeartbeatMonitor:
    def __init__(self, registry: NodeRegistry, timeout_seconds: float = 30.0, event_bus=None) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds
        self.event_bus = event_bus

    def beat(self, node_id: str):
        node = self.registry.get(node_id)
        if node:
            node.heartbeat()
            if self.event_bus is not None and hasattr(self.event_bus, "publish"):
                self.event_bus.publish("distributed.node.heartbeat", {"node_id": node_id}, topic="workflow.distributed", source="heartbeat")
        return node

    def scan(self):
        now = time.time()
        failed = []
        for node in self.registry.online():
            if node.last_heartbeat is not None and now - node.last_heartbeat > self.timeout_seconds:
                node.status = NodeStatus.FAILED
                failed.append(node)
        return failed

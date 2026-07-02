from __future__ import annotations
from .models import DistributionStrategy, DistributedNode
from .node_registry import NodeRegistry

class DistributedScheduler:
    def __init__(self, registry: NodeRegistry, strategy: DistributionStrategy | str = DistributionStrategy.LEAST_LOADED) -> None:
        self.registry = registry
        self.strategy = strategy if isinstance(strategy, DistributionStrategy) else DistributionStrategy(str(strategy))
        self._cursor = 0

    def select_node(self) -> DistributedNode | None:
        nodes = self.registry.available()
        if not nodes:
            return None
        if self.strategy == DistributionStrategy.ROUND_ROBIN:
            node = nodes[self._cursor % len(nodes)]
            self._cursor += 1
            return node
        if self.strategy == DistributionStrategy.PRIORITY:
            return sorted(nodes, key=lambda n: (-n.capacity, n.load, n.created_at))[0]
        return sorted(nodes, key=lambda n: (n.load, n.active_tasks, n.created_at))[0]

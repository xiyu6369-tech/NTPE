from __future__ import annotations
from .models import ClusterTopology
from .node_registry import NodeRegistry

class TopologyManager:
    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry

    def build(self) -> ClusterTopology:
        return ClusterTopology(nodes=[n.node_id for n in self.registry.all()], metadata={"online": len(self.registry.online())})

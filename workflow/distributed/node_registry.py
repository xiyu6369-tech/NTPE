from __future__ import annotations
from typing import Dict, List
from .models import DistributedNode, NodeStatus

class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: Dict[str, DistributedNode] = {}

    def register(self, node: DistributedNode) -> DistributedNode:
        self._nodes[node.node_id] = node
        return node

    def create(self, name: str, capacity: int = 1, **metadata) -> DistributedNode:
        return self.register(DistributedNode(name=name, capacity=capacity, metadata=dict(metadata)).online())

    def get(self, node_id: str) -> DistributedNode | None:
        return self._nodes.get(node_id)

    def all(self) -> List[DistributedNode]:
        return list(self._nodes.values())

    def online(self) -> List[DistributedNode]:
        return [n for n in self._nodes.values() if n.status in {NodeStatus.ONLINE, NodeStatus.BUSY}]

    def available(self) -> List[DistributedNode]:
        return [n for n in self.online() if n.available]

    def mark_failed(self, node_id: str, error: str | None = None) -> DistributedNode | None:
        node = self.get(node_id)
        if node:
            node.status = NodeStatus.FAILED
            node.metadata["error"] = error
        return node

    def manifest(self) -> dict:
        return {"node_count": len(self._nodes), "online_count": len(self.online()), "nodes": [n.to_dict() for n in self.all()]}

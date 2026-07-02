"""Distributed execution models for NTPE 1.0 Beta Stage-09.6.

This module is additive and keeps Foundation, CLI, SDK, Integration,
and Stage-09.0~09.5 workflow contracts stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List
import time
import uuid

DISTRIBUTED_EXECUTION_VERSION = "0.9.6"
DISTRIBUTED_EXECUTION_STAGE = "NTPE 1.0 Beta Stage-09.6 Distributed Execution"

class NodeStatus(str, Enum):
    CREATED = "created"
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"
    FAILED = "failed"
    DRAINING = "draining"

class DistributionStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY = "priority"

@dataclass
class DistributedNode:
    name: str
    capacity: int = 1
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: NodeStatus = NodeStatus.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float | None = None

    def online(self) -> "DistributedNode":
        self.status = NodeStatus.ONLINE
        self.heartbeat()
        return self

    def heartbeat(self) -> "DistributedNode":
        self.last_heartbeat = time.time()
        if self.status in {NodeStatus.CREATED, NodeStatus.OFFLINE}:
            self.status = NodeStatus.ONLINE
        return self

    @property
    def load(self) -> float:
        if self.capacity <= 0:
            return 1.0
        return min(1.0, self.active_tasks / self.capacity)

    @property
    def available(self) -> bool:
        return self.status in {NodeStatus.ONLINE, NodeStatus.BUSY} and self.active_tasks < self.capacity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "capacity": self.capacity,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "created_at": self.created_at,
            "last_heartbeat": self.last_heartbeat,
            "load": self.load,
        }

@dataclass
class DistributionResult:
    ok: bool
    task_id: str | None = None
    node_id: str | None = None
    status: str = "created"
    output: Any = None
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "task_id": self.task_id,
            "node_id": self.node_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "metadata": dict(self.metadata),
        }

@dataclass
class ClusterTopology:
    nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"nodes": list(self.nodes), "metadata": dict(self.metadata), "node_count": len(self.nodes)}

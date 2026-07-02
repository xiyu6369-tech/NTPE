"""Persistence models for NTPE 1.0 Beta Stage-09.5 Workflow Persistence.

This module is additive and keeps Foundation, CLI, SDK, Integration,
and Stage-09.0~09.4 workflow contracts stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
import time
import uuid

WORKFLOW_PERSISTENCE_VERSION = "0.9.5"
WORKFLOW_PERSISTENCE_STAGE = "NTPE 1.0 Beta Stage-09.5 Workflow Persistence"

class PersistenceStatus(str, Enum):
    CREATED = "created"
    SAVED = "saved"
    LOADED = "loaded"
    RECOVERED = "recovered"
    FAILED = "failed"

class SnapshotKind(str, Enum):
    WORKFLOW = "workflow"
    JOB = "job"
    TASK = "task"
    WORKER = "worker"
    RUNTIME = "runtime"
    CHECKPOINT = "checkpoint"

@dataclass
class WorkflowSnapshot:
    name: str
    kind: SnapshotKind | str = SnapshotKind.WORKFLOW
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    version: str = WORKFLOW_PERSISTENCE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.kind, SnapshotKind):
            self.kind = SnapshotKind(str(self.kind))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "name": self.name,
            "kind": self.kind.value,
            "state": dict(self.state),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowSnapshot":
        return cls(
            snapshot_id=data.get("snapshot_id", str(uuid.uuid4())),
            name=data.get("name", "snapshot"),
            kind=data.get("kind", SnapshotKind.WORKFLOW.value),
            state=dict(data.get("state", {})),
            metadata=dict(data.get("metadata", {})),
            created_at=float(data.get("created_at", time.time())),
            version=data.get("version", WORKFLOW_PERSISTENCE_VERSION),
        )

@dataclass
class Checkpoint:
    name: str
    snapshot_id: str
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "name": self.name,
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            checkpoint_id=data.get("checkpoint_id", str(uuid.uuid4())),
            name=data.get("name", "checkpoint"),
            snapshot_id=data.get("snapshot_id", ""),
            created_at=float(data.get("created_at", time.time())),
            metadata=dict(data.get("metadata", {})),
        )

@dataclass
class PersistenceResult:
    ok: bool
    status: PersistenceStatus
    snapshot: WorkflowSnapshot | None = None
    checkpoint: Checkpoint | None = None
    error: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status.value,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "error": self.error,
        }

"""Checkpoint manager for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
from typing import Dict, Iterable
from .persistence_models import Checkpoint, WorkflowSnapshot

class CheckpointManager:
    def __init__(self) -> None:
        self.checkpoints: Dict[str, Checkpoint] = {}

    def create(self, name: str, snapshot: WorkflowSnapshot, **metadata) -> Checkpoint:
        checkpoint = Checkpoint(name=name, snapshot_id=snapshot.snapshot_id, metadata=dict(metadata))
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint

    def latest(self) -> Checkpoint | None:
        if not self.checkpoints:
            return None
        return max(self.checkpoints.values(), key=lambda checkpoint: checkpoint.created_at)

    def all(self) -> Iterable[Checkpoint]:
        return list(self.checkpoints.values())

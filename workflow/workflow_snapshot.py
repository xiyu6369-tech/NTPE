"""Workflow snapshot helpers for NTPE Stage-09.5."""
from __future__ import annotations
from typing import Any, Dict
from .persistence_models import WorkflowSnapshot, SnapshotKind

class WorkflowSnapshotBuilder:
    def build(self, name: str, *, kind: SnapshotKind | str = SnapshotKind.WORKFLOW, state: Dict[str, Any] | None = None, metadata: Dict[str, Any] | None = None) -> WorkflowSnapshot:
        return WorkflowSnapshot(name=name, kind=kind, state=dict(state or {}), metadata=dict(metadata or {}))

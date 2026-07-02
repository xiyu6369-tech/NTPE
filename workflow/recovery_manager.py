"""Recovery manager for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
from typing import Any, Dict
from .persistence_models import PersistenceResult, PersistenceStatus, WorkflowSnapshot

class RecoveryManager:
    def recover(self, snapshot: WorkflowSnapshot, target: Any | None = None) -> PersistenceResult:
        if target is not None:
            if hasattr(target, "metadata") and isinstance(getattr(target, "metadata"), dict):
                target.metadata.update(snapshot.metadata)
            if hasattr(target, "recovered_state"):
                target.recovered_state = dict(snapshot.state)
        return PersistenceResult(ok=True, status=PersistenceStatus.RECOVERED, snapshot=snapshot)

    def state(self, snapshot: WorkflowSnapshot) -> Dict[str, Any]:
        return dict(snapshot.state)

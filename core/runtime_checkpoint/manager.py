"""RM-6.3.2 Runtime Checkpoint Manager.

Provides checkpoint lifecycle operations: create, load, validate,
restore, list, and delete — all in-memory. No network calls.
No provider imports. No file persistence. No Translation Engine
modifications.

Architecture:
    TranslationRequest
            │
            ▼
    RuntimeSessionManager
            │
            ▼
    RuntimeCheckpointManager
            │
            ├── CheckpointSnapshot
            ├── ProgressState
            ├── RequestManifest
            └── RecoveryPoint
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from core.runtime_checkpoint.models import (
    CheckpointSnapshot,
    CheckpointIntegrityError,
    CheckpointNotFoundError,
    CheckpointSessionMismatchError,
    CheckpointSnapshotMismatchError,
    ProgressState,
    ProgressStatus,
    RequestManifest,
    utc_now_iso,
)
from core.runtime_checkpoint.validator import CheckpointValidator


class RuntimeCheckpointManager:
    """Create, load, validate, restore, list, and delete checkpoints."""

    version = "rm-6.3.2"

    def __init__(self, validator: Optional[CheckpointValidator] = None):
        self._checkpoints: Dict[str, Dict[str, CheckpointSnapshot]] = {}
        self._validator = validator or CheckpointValidator()

    def create_checkpoint(
        self,
        session_id: str,
        *,
        chunk_index: int = 0,
        progress: Optional[ProgressState] = None,
        manifest: Optional[RequestManifest] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointSnapshot:
        checkpoint = CheckpointSnapshot(
            session_id=session_id,
            chunk_index=chunk_index,
            progress=progress or ProgressState(),
            manifest=manifest,
            metadata=dict(metadata or {}),
        )
        checkpoint = checkpoint.with_hash()
        self._checkpoints.setdefault(session_id, {})[checkpoint.checkpoint_id] = checkpoint
        return checkpoint

    def load_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
    ) -> CheckpointSnapshot:
        session_checkpoints = self._checkpoints.get(session_id)
        if session_checkpoints is None:
            raise CheckpointNotFoundError(checkpoint_id)
        checkpoint = session_checkpoints.get(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(checkpoint_id)
        return checkpoint

    def validate_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
    ) -> CheckpointSnapshot:
        checkpoint = self.load_checkpoint(session_id, checkpoint_id)
        self._validator.validate(checkpoint, session_id)
        return checkpoint

    def restore_session(
        self,
        session_id: str,
        checkpoint_id: str,
        restore_fn: Callable[[CheckpointSnapshot], Any],
    ) -> CheckpointSnapshot:
        checkpoint = self.validate_checkpoint(session_id, checkpoint_id)
        restore_fn(checkpoint)
        return checkpoint

    def list_checkpoints(
        self,
        session_id: str,
    ) -> List[CheckpointSnapshot]:
        session_checkpoints = self._checkpoints.get(session_id, {})
        return sorted(
            session_checkpoints.values(),
            key=lambda c: c.created_at,
        )

    def latest_checkpoint(
        self,
        session_id: str,
    ) -> Optional[CheckpointSnapshot]:
        checkpoints = self.list_checkpoints(session_id)
        if not checkpoints:
            return None
        return checkpoints[-1]

    def delete_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
    ) -> None:
        session_checkpoints = self._checkpoints.get(session_id)
        if session_checkpoints is None:
            raise CheckpointNotFoundError(checkpoint_id)
        if checkpoint_id not in session_checkpoints:
            raise CheckpointNotFoundError(checkpoint_id)
        del session_checkpoints[checkpoint_id]
        if not session_checkpoints:
            del self._checkpoints[session_id]

    @property
    def active_sessions(self) -> int:
        return len(self._checkpoints)

    @property
    def total_checkpoints(self) -> int:
        return sum(len(v) for v in self._checkpoints.values())

    def recover(
        self,
        session_id: str,
        restore_fn: Callable[[CheckpointSnapshot], Any],
    ) -> Optional[CheckpointSnapshot]:
        checkpoint = self.latest_checkpoint(session_id)
        if checkpoint is None:
            return None
        self.validate_checkpoint(session_id, checkpoint.checkpoint_id)
        restore_fn(checkpoint)
        return checkpoint


__all__ = [
    "RuntimeCheckpointManager",
    "CheckpointNotFoundError",
    "CheckpointSessionMismatchError",
    "CheckpointIntegrityError",
    "CheckpointSnapshotMismatchError",
]
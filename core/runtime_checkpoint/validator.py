"""RM-6.3.2 Checkpoint Validator.

Validates checkpoint integrity, session match, snapshot match, and
metadata consistency. No provider imports. No network calls.
"""

from __future__ import annotations

from typing import Any, Dict

from core.runtime_checkpoint.models import (
    CheckpointSnapshot,
    CheckpointIntegrityError,
    CheckpointNotFoundError,
    CheckpointSessionMismatchError,
    CheckpointSnapshotMismatchError,
)


class CheckpointValidator:
    """Validate checkpoint integrity and consistency."""

    version = "rm-6.3.2"

    def validate(self, snapshot: CheckpointSnapshot, session_id: str) -> CheckpointSnapshot:
        self._validate_session(snapshot, session_id)
        self._validate_hash(snapshot)
        self._validate_metadata(snapshot)
        return snapshot

    def _validate_hash(self, snapshot: CheckpointSnapshot) -> None:
        if not snapshot.state_hash:
            raise CheckpointIntegrityError(snapshot.checkpoint_id)
        computed = snapshot.compute_hash()
        if computed != snapshot.state_hash:
            raise CheckpointIntegrityError(snapshot.checkpoint_id)

    def _validate_session(self, snapshot: CheckpointSnapshot, session_id: str) -> None:
        if snapshot.session_id != session_id:
            raise CheckpointSessionMismatchError(
                snapshot.checkpoint_id,
                expected=session_id,
                actual=snapshot.session_id,
            )

    def _validate_snapshot_match(
        self,
        checkpoint: CheckpointSnapshot,
        expected_snapshot_id: str,
    ) -> None:
        if checkpoint.snapshot_id != expected_snapshot_id:
            raise CheckpointSnapshotMismatchError(
                checkpoint.checkpoint_id,
                expected=expected_snapshot_id,
                actual=checkpoint.snapshot_id,
            )

    def _validate_metadata(self, snapshot: CheckpointSnapshot) -> None:
        if snapshot.metadata is None:
            raise CheckpointIntegrityError(snapshot.checkpoint_id)

    def validate_snapshot_match(
        self,
        checkpoint: CheckpointSnapshot,
        expected_snapshot_id: str,
    ) -> CheckpointSnapshot:
        self._validate_snapshot_match(checkpoint, expected_snapshot_id)
        return checkpoint

    def validate_session_match(
        self,
        checkpoint: CheckpointSnapshot,
        expected_session_id: str,
    ) -> CheckpointSnapshot:
        self._validate_session(checkpoint, expected_session_id)
        return checkpoint

    def validate_chain(
        self,
        checkpoints: list[CheckpointSnapshot],
    ) -> bool:
        if not checkpoints:
            return True
        for cp in checkpoints:
            self._validate_hash(cp)
            self._validate_metadata(cp)
        return True


__all__ = [
    "CheckpointValidator",
]
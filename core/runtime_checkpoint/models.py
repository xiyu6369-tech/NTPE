"""RM-6.3.2 Runtime Checkpoint domain models.

Immutable dataclasses for checkpoint snapshots, progress state tracking,
and request manifest recording. No provider imports. No network calls.
No persistence. No Translation Engine modifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checkpoint_hash(*parts: str) -> str:
    joined = "\x00".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()


def _generate_checkpoint_id() -> str:
    raw = uuid4().hex
    return raw[:12]


def _generate_snapshot_id() -> str:
    raw = uuid4().hex
    return f"snap-{raw[:8]}"


class ProgressStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ProgressState:
    """Describe translation progress within a checkpoint.

    Tracks the current chunk index, completed chunk count, total
    chunks, and execution status. Immutable — safe for concurrent
    reads without locks.
    """

    current_chunk: int = 0
    completed_chunks: int = 0
    total_chunks: int = 0
    status: ProgressStatus = ProgressStatus.ACTIVE


@dataclass(frozen=True)
class RequestManifest:
    """Record runtime request associations within a checkpoint.

    Stores the identity of a request (request_hash, prompt_hash),
    the associated snapshot, and the chunk index. No provider
    payload, no translated text, no API response is stored.
    """

    request_hash: str
    prompt_hash: str
    snapshot_id: str
    chunk_index: int


@dataclass(frozen=True)
class CheckpointSnapshot:
    """Immutable container for a single checkpoint snapshot.

    Uniquely identifies a checkpoint via checkpoint_id and
    snapshot_id. Contains session identity, chunk progress,
    creation time, and a deterministic state_hash for integrity
    verification. Metadata carries arbitrary session-private
    runtime metadata.
    """

    checkpoint_id: str = field(default_factory=_generate_checkpoint_id)
    session_id: str = ""
    snapshot_id: str = field(default_factory=_generate_snapshot_id)
    chunk_index: int = 0
    created_at: str = field(default_factory=utc_now_iso)
    state_hash: str = ""
    progress: ProgressState = field(default_factory=ProgressState)
    manifest: Optional[RequestManifest] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.3.2"

    def compute_hash(self) -> str:
        """Compute a deterministic integrity hash from the checkpoint fields.

        The hash covers all identity and progress fields but excludes
        the created_at timestamp so that identical checkpoints
        created at different times produce the same hash.
        """
        parts: List[str] = [
            self.checkpoint_id,
            self.session_id,
            self.snapshot_id,
            str(self.chunk_index),
            str(self.progress.current_chunk),
            str(self.progress.completed_chunks),
            str(self.progress.total_chunks),
            self.progress.status.value,
            str(self.metadata),
        ]
        if self.manifest is not None:
            parts.extend([
                self.manifest.request_hash,
                self.manifest.prompt_hash,
                self.manifest.snapshot_id,
                str(self.manifest.chunk_index),
            ])
        return _checkpoint_hash(*parts)

    def with_hash(self) -> CheckpointSnapshot:
        """Return a new CheckpointSnapshot with an updated state_hash."""
        return CheckpointSnapshot(
            checkpoint_id=self.checkpoint_id,
            session_id=self.session_id,
            snapshot_id=self.snapshot_id,
            chunk_index=self.chunk_index,
            created_at=self.created_at,
            state_hash=self.compute_hash(),
            progress=self.progress,
            manifest=self.manifest,
            metadata=self.metadata,
        )


class CheckpointIntegrityError(ValueError):
    def __init__(self, checkpoint_id: str):
        msg = f"Integrity check failed for checkpoint: {checkpoint_id}"
        super().__init__(msg)
        self.checkpoint_id = checkpoint_id


class CheckpointNotFoundError(ValueError):
    def __init__(self, checkpoint_id: str):
        msg = f"Checkpoint not found: {checkpoint_id}"
        super().__init__(msg)
        self.checkpoint_id = checkpoint_id


class CheckpointSessionMismatchError(ValueError):
    def __init__(self, checkpoint_id: str, expected: str, actual: str):
        msg = (
            f"Checkpoint session mismatch for {checkpoint_id}: "
            f"expected {expected}, got {actual}"
        )
        super().__init__(msg)
        self.checkpoint_id = checkpoint_id
        self.expected_session = expected
        self.actual_session = actual


class CheckpointSnapshotMismatchError(ValueError):
    def __init__(self, checkpoint_id: str, expected: str, actual: str):
        msg = (
            f"Checkpoint snapshot mismatch for {checkpoint_id}: "
            f"expected {expected}, got {actual}"
        )
        super().__init__(msg)
        self.checkpoint_id = checkpoint_id
        self.expected_snapshot = expected
        self.actual_snapshot = actual


__all__ = [
    "CheckpointSnapshot",
    "ProgressState",
    "ProgressStatus",
    "RequestManifest",
    "CheckpointIntegrityError",
    "CheckpointNotFoundError",
    "CheckpointSessionMismatchError",
    "CheckpointSnapshotMismatchError",
    "_checkpoint_hash",
    "_generate_checkpoint_id",
    "_generate_snapshot_id",
    "utc_now_iso",
]
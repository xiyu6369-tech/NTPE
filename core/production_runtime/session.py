"""NTPE 1.0 Beta Stage-01 Production Runtime sessions."""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .checkpoint import RuntimeCheckpoint, RuntimeCheckpointStore


@dataclass
class RuntimeSession:
    session_id: str = field(default_factory=lambda: f"session-{uuid.uuid4().hex[:12]}")
    job_id: str = "default-job"
    status: str = "created"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


class RuntimeSessionManager:
    """Session lock, checkpoint and resume manager."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self, checkpoint_store: Optional[RuntimeCheckpointStore] = None):
        self.checkpoint_store = checkpoint_store or RuntimeCheckpointStore()
        self._lock = threading.RLock()
        self.current: Optional[RuntimeSession] = None

    def create(self, job_id: str = "default-job", session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> RuntimeSession:
        with self._lock:
            self.current = RuntimeSession(session_id=session_id or f"session-{uuid.uuid4().hex[:12]}", job_id=job_id, metadata=dict(metadata or {}))
            return self.current

    def start(self) -> RuntimeSession:
        with self._lock:
            session = self._ensure()
            session.status = "running"
            session.updated_at = time.time()
            return session

    def complete(self) -> RuntimeSession:
        with self._lock:
            session = self._ensure()
            session.status = "completed"
            session.updated_at = time.time()
            return session

    def fail(self, error: Any) -> RuntimeSession:
        with self._lock:
            session = self._ensure()
            session.status = "failed"
            session.metadata["last_error"] = str(error)
            session.updated_at = time.time()
            return session

    def checkpoint(self, segment_index: int = 0, state: Optional[Dict[str, Any]] = None) -> RuntimeCheckpoint:
        session = self._ensure()
        checkpoint = RuntimeCheckpoint(
            checkpoint_id=f"{session.session_id}:{int(segment_index)}",
            session_id=session.session_id,
            job_id=session.job_id,
            segment_index=int(segment_index),
            state=dict(state or {}),
        )
        return self.checkpoint_store.save(checkpoint)

    def resume(self, session_id: str) -> Optional[RuntimeCheckpoint]:
        return self.checkpoint_store.load(session_id)

    def _ensure(self) -> RuntimeSession:
        if self.current is None:
            self.current = RuntimeSession()
        return self.current

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "production_runtime_session_manager",
            "version": self.version,
            "current": self.current.to_dict() if self.current else None,
            "checkpoint_store": self.checkpoint_store.manifest(),
        }


__all__ = ["RuntimeSession", "RuntimeSessionManager"]

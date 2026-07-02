from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.production_runtime.checkpoint import RuntimeCheckpoint, RuntimeCheckpointStore
from core.production_runtime.session import RuntimeSession, RuntimeSessionManager


@dataclass
class CLISessionRecord:
    session_id: str
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CLISessionRecord":
        return cls(
            session_id=str(data.get("session_id") or f"session-{uuid.uuid4().hex[:12]}"),
            job_id=str(data.get("job_id") or "default-job"),
            status=str(data.get("status") or "created"),
            created_at=float(data.get("created_at") or time.time()),
            updated_at=float(data.get("updated_at") or time.time()),
            metadata=dict(data.get("metadata") or {}),
        )


class CLISessionStore:
    """Small JSON-backed session index used by CLI session commands.

    The store is intentionally separate from the frozen Foundation contracts and
    uses Production Runtime checkpoint primitives for checkpoint/restore.
    """

    version = "ntpe-1.0-beta-stage-06.5"

    def __init__(self, root: Path, session_dir: str = "sessions") -> None:
        self.root = Path(root).resolve()
        self.session_dir = self.root / session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir = self.root / ".ntpe_runtime_checkpoints"
        self.checkpoint_store = RuntimeCheckpointStore(str(self.checkpoint_dir))
        self.runtime_sessions = RuntimeSessionManager(self.checkpoint_store)

    def _path(self, session_id: str) -> Path:
        safe = str(session_id or "default").replace("/", "_").replace("\\", "_")
        return self.session_dir / f"{safe}.json"

    def create(self, session_id: Optional[str] = None, job_id: str = "default-job", metadata: Optional[Dict[str, Any]] = None) -> CLISessionRecord:
        record = CLISessionRecord(
            session_id=session_id or f"session-{uuid.uuid4().hex[:12]}",
            job_id=job_id,
            status="created",
            metadata=dict(metadata or {}),
        )
        runtime_session = self.runtime_sessions.create(job_id=record.job_id, session_id=record.session_id, metadata=record.metadata)
        record.metadata.setdefault("runtime_session", runtime_session.to_dict())
        return self.save(record)

    def save(self, record: CLISessionRecord) -> CLISessionRecord:
        record.updated_at = time.time()
        self._path(record.session_id).write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def load(self, session_id: str) -> Optional[CLISessionRecord]:
        path = self._path(session_id)
        if not path.exists():
            return None
        return CLISessionRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def require(self, session_id: str) -> CLISessionRecord:
        record = self.load(session_id)
        if record is None:
            raise FileNotFoundError(f"session not found: {session_id}")
        return record

    def list(self, status: Optional[str] = None) -> List[CLISessionRecord]:
        records: List[CLISessionRecord] = []
        for path in sorted(self.session_dir.glob("*.json")):
            try:
                record = CLISessionRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if status and record.status != status:
                continue
            records.append(record)
        return records

    def update_status(self, session_id: str, status: str, **metadata: Any) -> CLISessionRecord:
        record = self.require(session_id)
        record.status = status
        record.metadata.update(metadata)
        return self.save(record)

    def checkpoint(self, session_id: str, segment_index: int = 0, state: Optional[Dict[str, Any]] = None) -> RuntimeCheckpoint:
        record = self.require(session_id)
        checkpoint = RuntimeCheckpoint(
            checkpoint_id=f"{record.session_id}:{int(segment_index)}",
            session_id=record.session_id,
            job_id=record.job_id,
            segment_index=int(segment_index),
            state=dict(state or {}),
        )
        saved = self.checkpoint_store.save(checkpoint)
        record.metadata["last_checkpoint"] = saved.to_dict()
        self.save(record)
        return saved

    def restore(self, session_id: str) -> Optional[RuntimeCheckpoint]:
        return self.checkpoint_store.load(session_id)

    def cleanup(self, statuses: Optional[Iterable[str]] = None, all_sessions: bool = False) -> Dict[str, Any]:
        allowed = set(statuses or [])
        deleted: List[str] = []
        for record in self.list():
            if not all_sessions and allowed and record.status not in allowed:
                continue
            if not all_sessions and not allowed and record.status not in {"completed", "stopped", "failed"}:
                continue
            path = self._path(record.session_id)
            if path.exists():
                path.unlink()
                deleted.append(record.session_id)
            self.checkpoint_store.delete(record.session_id)
        return {"deleted": deleted, "deleted_count": len(deleted)}

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "cli_session_store",
            "version": self.version,
            "session_dir": str(self.session_dir),
            "checkpoint_dir": str(self.checkpoint_dir),
            "production_runtime": self.runtime_sessions.manifest(),
        }


def ensure_demo_session(store: CLISessionStore, job_id: str = "demo-job") -> CLISessionRecord:
    records = store.list()
    if records:
        return records[0]
    return store.create(job_id=job_id, metadata={"created_by": "cli_session_command"})


__all__ = ["CLISessionRecord", "CLISessionStore", "ensure_demo_session"]

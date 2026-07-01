"""NTPE 1.0 Beta Stage-01 Production Runtime checkpoint support."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RuntimeCheckpoint:
    checkpoint_id: str
    session_id: str
    job_id: str
    segment_index: int = 0
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "segment_index": self.segment_index,
            "state": dict(self.state),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeCheckpoint":
        return cls(
            checkpoint_id=str(data.get("checkpoint_id") or "checkpoint"),
            session_id=str(data.get("session_id") or "default"),
            job_id=str(data.get("job_id") or "job"),
            segment_index=int(data.get("segment_index") or 0),
            state=dict(data.get("state") or {}),
            created_at=float(data.get("created_at") or time.time()),
        )


class RuntimeCheckpointStore:
    """JSON checkpoint store. Dependency-free and safe for incremental adoption."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self, root_dir: str = ".ntpe_runtime_checkpoints"):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        safe = str(session_id or "default").replace(os.sep, "_")
        return os.path.join(self.root_dir, f"{safe}.json")

    def save(self, checkpoint: RuntimeCheckpoint) -> RuntimeCheckpoint:
        with open(self._path(checkpoint.session_id), "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)
        return checkpoint

    def load(self, session_id: str) -> Optional[RuntimeCheckpoint]:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return RuntimeCheckpoint.from_dict(json.load(f))

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    def manifest(self) -> Dict[str, Any]:
        return {"name": "production_runtime_checkpoint_store", "version": self.version, "root_dir": self.root_dir}


__all__ = ["RuntimeCheckpoint", "RuntimeCheckpointStore"]

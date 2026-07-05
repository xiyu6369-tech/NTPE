from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from core.translation_engine.utils import now_iso, save_json


@dataclass
class SessionCheckpoint:
    session_id: str
    status: str = "created"
    cursor: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def checkpoint_path(root: str | Path, session_id: str) -> Path:
    return Path(root) / ".ntpe_sessions" / session_id / "session_checkpoint.json"


def save_checkpoint(root: str | Path, checkpoint: SessionCheckpoint) -> Path:
    checkpoint.updated_at = now_iso()
    path = checkpoint_path(root, checkpoint.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, checkpoint.to_dict())
    return path


def load_checkpoint(root: str | Path, session_id: str) -> SessionCheckpoint | None:
    path = checkpoint_path(root, session_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return SessionCheckpoint(**data)

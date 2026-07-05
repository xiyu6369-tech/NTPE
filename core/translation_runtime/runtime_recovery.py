from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.translation_engine.utils import load_json, now_iso, save_json


RECOVERY_VERSION = "1.2-professional-stage-04"
DEFAULT_RECOVERY_DIRNAME = ".ntpe_runtime_checkpoints"


@dataclass(frozen=True)
class RuntimeCheckpointKey:
    """Stable checkpoint key used by TXT, batch, and future UI/SDK layers."""

    scope: str
    name: str

    @property
    def safe_name(self) -> str:
        raw = f"{self.scope}:{self.name}"
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw)[:80]
        return f"{sanitized}_{digest}"


@dataclass
class RuntimeCheckpoint:
    key: RuntimeCheckpointKey
    status: str = "running"
    cursor: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    version: str = RECOVERY_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["key"] = asdict(self.key)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeCheckpoint":
        key_data = data.get("key") or {}
        key = RuntimeCheckpointKey(scope=str(key_data.get("scope", "runtime")), name=str(key_data.get("name", "default")))
        return cls(
            key=key,
            status=str(data.get("status", "running")),
            cursor=dict(data.get("cursor") or {}),
            metadata=dict(data.get("metadata") or {}),
            errors=list(data.get("errors") or []),
            created_at=str(data.get("created_at") or now_iso()),
            updated_at=str(data.get("updated_at") or now_iso()),
            version=str(data.get("version") or RECOVERY_VERSION),
        )


def checkpoint_path(root: str | Path, key: RuntimeCheckpointKey, dirname: str = DEFAULT_RECOVERY_DIRNAME) -> Path:
    return Path(root) / dirname / f"{key.safe_name}.json"


def load_checkpoint(root: str | Path, key: RuntimeCheckpointKey) -> RuntimeCheckpoint:
    path = checkpoint_path(root, key)
    if not path.exists():
        return RuntimeCheckpoint(key=key)
    try:
        data = load_json(path)
    except Exception:
        return RuntimeCheckpoint(key=key, status="corrupt", errors=[{"code": "CHECKPOINT_CORRUPT", "message": str(path)}])
    if not isinstance(data, dict):
        return RuntimeCheckpoint(key=key, status="corrupt", errors=[{"code": "CHECKPOINT_INVALID", "message": str(path)}])
    return RuntimeCheckpoint.from_dict(data)


def save_checkpoint(root: str | Path, checkpoint: RuntimeCheckpoint) -> Path:
    checkpoint.updated_at = now_iso()
    path = checkpoint_path(root, checkpoint.key)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, checkpoint.to_dict())
    return path


def update_checkpoint(
    root: str | Path,
    key: RuntimeCheckpointKey,
    *,
    status: str | None = None,
    cursor: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> RuntimeCheckpoint:
    checkpoint = load_checkpoint(root, key)
    if status is not None:
        checkpoint.status = status
    if cursor:
        checkpoint.cursor.update(cursor)
    if metadata:
        checkpoint.metadata.update(metadata)
    if error:
        checkpoint.errors.append(error)
    save_checkpoint(root, checkpoint)
    return checkpoint


def mark_checkpoint_completed(root: str | Path, key: RuntimeCheckpointKey, metadata: dict[str, Any] | None = None) -> RuntimeCheckpoint:
    return update_checkpoint(root, key, status="success", metadata=metadata or {})


def recovery_summary(root: str | Path, dirname: str = DEFAULT_RECOVERY_DIRNAME) -> dict[str, Any]:
    directory = Path(root) / dirname
    files = sorted(directory.glob("*.json")) if directory.exists() else []
    checkpoints: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for path in files:
        try:
            data = load_json(path)
            if not isinstance(data, dict):
                raise ValueError("checkpoint payload is not a dict")
            status = str(data.get("status", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
            checkpoints.append({
                "path": str(path),
                "status": status,
                "key": data.get("key", {}),
                "cursor": data.get("cursor", {}),
                "updated_at": data.get("updated_at", ""),
            })
        except Exception as exc:
            status_counts["corrupt"] = status_counts.get("corrupt", 0) + 1
            checkpoints.append({"path": str(path), "status": "corrupt", "error": str(exc)})
    return {
        "status": "success",
        "version": RECOVERY_VERSION,
        "checkpoint_dir": str(directory),
        "total": len(checkpoints),
        "status_counts": status_counts,
        "checkpoints": checkpoints,
    }

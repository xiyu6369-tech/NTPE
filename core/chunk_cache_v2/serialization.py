from __future__ import annotations
import json, os
from pathlib import Path
from .fingerprint import canonical_json
from .store import ChunkCacheStore
from .validation import ChunkCacheValidationError


def serialize_cache_store(store):return canonical_json(store.to_dict())
def deserialize_cache_store(payload):
    try:data=json.loads(payload)
    except (json.JSONDecodeError,UnicodeDecodeError) as exc:raise ChunkCacheValidationError("invalid cache JSON") from exc
    if not isinstance(data,dict):raise ChunkCacheValidationError("cache JSON must be object")
    return ChunkCacheStore.from_dict(data)
def _resolve_cache_path(path, *, allowed_root):
    if allowed_root is None:
        raise ChunkCacheValidationError("allowed_root is required")
    root = Path(allowed_root)
    if ".." in root.parts:
        raise ChunkCacheValidationError("allowed_root traversal rejected")
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise ChunkCacheValidationError("allowed_root must be a directory")
    resolved_root = root.resolve(strict=True)
    supplied = Path(path)
    if ".." in supplied.parts:
        raise ChunkCacheValidationError("path traversal rejected")
    candidate = supplied if supplied.is_absolute() else resolved_root / supplied
    resolved_target = candidate.resolve(strict=False)
    if resolved_target == resolved_root:
        raise ChunkCacheValidationError("cache target must be a file below allowed_root")
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise ChunkCacheValidationError("cache path escapes allowed_root") from exc
    return resolved_target, resolved_root


def save_cache_store(path, store, *, allowed_root):
    target, resolved_root = _resolve_cache_path(path, allowed_root=allowed_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Re-resolve after directory creation so a pre-existing symlink cannot redirect the write.
    target, _ = _resolve_cache_path(target, allowed_root=resolved_root)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(serialize_cache_store(store), encoding="utf-8", newline="\n")
    deserialize_cache_store(temporary.read_bytes())
    os.replace(temporary, target)


def load_cache_store(path, *, allowed_root):
    target, _ = _resolve_cache_path(path, allowed_root=allowed_root)
    return deserialize_cache_store(target.read_bytes())

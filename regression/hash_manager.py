"""Stable hash helpers for regression manifests."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache"}

def stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def directory_hash(root: str | Path, max_files: int = 5000) -> str:
    root = Path(root)
    entries = []
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            entries.append((rel, file_hash(path)))
            if len(entries) >= max_files:
                break
    return stable_json_hash(entries)

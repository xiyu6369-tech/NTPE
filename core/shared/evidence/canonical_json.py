"""Canonical JSON helpers for deterministic evidence artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


_JSON_OPTIONS = {
    "allow_nan": False,
    "ensure_ascii": False,
    "separators": (",", ":"),
    "sort_keys": True,
}


def canonical_json_text(value: object) -> str:
    """Serialize *value* with the frozen shared evidence JSON contract."""
    return json.dumps(value, **_JSON_OPTIONS)


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes without a trailing newline."""
    return canonical_json_text(value).encode("utf-8")


def write_canonical_json(path: Path, value: object) -> None:
    """Atomically replace *path* with canonical JSON from a same-dir temp file."""
    destination = Path(path)
    payload = canonical_json_bytes(value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json(path: Path) -> object:
    """Read a UTF-8 JSON document without coercing its values."""
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


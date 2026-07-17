from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_review_artifact(payload: Mapping[str, object]) -> Mapping[str, object]:
    safe = dict(payload)
    forbidden = {"api_key", "secret", "prompt", "full_document", "filesystem_path", "resume_state"}
    if forbidden & set(safe):
        raise ValueError("forbidden_artifact_field")
    return MappingProxyType(safe)


def write_review_artifact(directory: str | Path, artifact: Mapping[str, object]) -> tuple[str, str]:
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(artifact)) + "\n").encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    destination = (root / f"review-{digest[:24]}.json").resolve()
    if destination.parent != root:
        raise ValueError("unsafe_artifact_path")
    temporary = root / f".{destination.name}.tmp-{os.getpid()}"
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return str(destination), digest

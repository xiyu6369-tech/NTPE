from __future__ import annotations

import hashlib
import json
from pathlib import Path


def resolve_reference(root: str | Path, reference: str) -> Path:
    path = Path(reference)
    return path if path.is_absolute() else Path(root) / path


def reference_sha256(root: str | Path, reference: str) -> str:
    return hashlib.sha256(resolve_reference(root, reference).read_bytes()).hexdigest()


def load_reference(root: str | Path, reference: str) -> dict[str, object]:
    return json.loads(resolve_reference(root, reference).read_text(encoding="utf-8"))


"""Extension manifest helpers for NTPE Stage-08.4."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .extension_models import ExtensionManifest


def build_extension_manifest(name: str, *, version: str = "1.0.0", entrypoint: str = "", capabilities: list[str] | None = None, kind: str = "extension", **metadata: Any) -> ExtensionManifest:
    manifest = ExtensionManifest(name=name, version=version, entrypoint=entrypoint, capabilities=list(capabilities or []), kind=kind, metadata=dict(metadata))
    manifest.validate()
    return manifest


def load_extension_manifest(path: str | Path) -> ExtensionManifest:
    data: Dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest = ExtensionManifest(**data)
    manifest.validate()
    return manifest

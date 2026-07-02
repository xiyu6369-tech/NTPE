from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CLIContext:
    """Runtime context shared by CLI commands."""

    root: Path = field(default_factory=lambda: Path.cwd())
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def discover(cls, start: Optional[Path] = None) -> "CLIContext":
        base = (start or Path.cwd()).resolve()
        current = base
        markers = ("VERSION.txt", "core", "translation", "runtime")
        while True:
            if any((current / marker).exists() for marker in markers):
                return cls(root=current)
            if current.parent == current:
                return cls(root=base)
            current = current.parent

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def read_version(self, default: str = "unknown") -> str:
        version_file = self.path("VERSION.txt")
        if version_file.exists():
            value = version_file.read_text(encoding="utf-8", errors="ignore").strip()
            return value or default
        return default

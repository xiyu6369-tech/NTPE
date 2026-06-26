from __future__ import annotations

from pathlib import Path


def ensure_dirs(*paths: str | Path) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

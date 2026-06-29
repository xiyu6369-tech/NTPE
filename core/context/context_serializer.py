from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ContextSerializer:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.context_dir = self.root / "context"
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name: str, default):
        path = self.context_dir / name
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return default

    def save(self, name: str, data: dict) -> Path:
        path = self.context_dir / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

"""Persistence store for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable

class PersistenceStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else None
        self.memory: Dict[str, str] = {}
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace("\\", "_")
        assert self.root is not None
        return self.root / f"{safe}.json"

    def save(self, key: str, value: str) -> None:
        self.memory[key] = value
        if self.root is not None:
            self._path(key).write_text(value, encoding="utf-8")

    def load(self, key: str) -> str:
        if key in self.memory:
            return self.memory[key]
        if self.root is not None:
            path = self._path(key)
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.memory[key] = text
                return text
        raise KeyError(key)

    def exists(self, key: str) -> bool:
        if key in self.memory:
            return True
        return self.root is not None and self._path(key).exists()

    def keys(self) -> Iterable[str]:
        seen = set(self.memory)
        if self.root is not None:
            for path in self.root.glob("*.json"):
                seen.add(path.stem)
        return sorted(seen)

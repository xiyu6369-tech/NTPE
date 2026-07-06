# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

from .translation_memory_entry import TranslationMemoryEntry
from .translation_memory_index import TranslationMemoryIndex


class TranslationMemoryStore:
    def __init__(self, entries: Iterable[TranslationMemoryEntry] | None = None) -> None:
        self._entries: Dict[str, TranslationMemoryEntry] = {}
        self.index = TranslationMemoryIndex()
        for entry in entries or []:
            self.add(entry)

    def add(self, entry: TranslationMemoryEntry) -> TranslationMemoryEntry:
        assert entry.entry_id is not None
        old = self._entries.get(entry.entry_id)
        if old is not None:
            self.index.remove(old)
        self._entries[entry.entry_id] = entry
        self.index.add(entry)
        return entry

    def get(self, entry_id: str) -> TranslationMemoryEntry | None:
        return self._entries.get(entry_id)

    def all(self) -> List[TranslationMemoryEntry]:
        return list(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[TranslationMemoryEntry]:
        return iter(self._entries.values())

    def to_dict(self) -> Dict[str, object]:
        return {"entries": [entry.to_dict() for entry in self.all()]}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "TranslationMemoryStore":
        return cls(TranslationMemoryEntry.from_dict(item) for item in data.get("entries", []))

    def export_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def import_json(cls, path: str | Path) -> "TranslationMemoryStore":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

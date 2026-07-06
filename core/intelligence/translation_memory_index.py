# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set
import re

from .translation_memory_entry import TranslationMemoryEntry, normalize_memory_text

TOKEN_RE = re.compile(r"[\w\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]+", re.UNICODE)


def memory_tokens(text: str) -> List[str]:
    return TOKEN_RE.findall(normalize_memory_text(text))


class TranslationMemoryIndex:
    def __init__(self) -> None:
        self._tokens: Dict[str, Set[str]] = defaultdict(set)
        self._exact: Dict[str, str] = {}

    def add(self, entry: TranslationMemoryEntry) -> None:
        assert entry.entry_id is not None
        self._exact[entry.normalized_source] = entry.entry_id
        for token in memory_tokens(entry.source_text):
            self._tokens[token].add(entry.entry_id)

    def remove(self, entry: TranslationMemoryEntry) -> None:
        if entry.normalized_source in self._exact:
            self._exact.pop(entry.normalized_source, None)
        for token in memory_tokens(entry.source_text):
            self._tokens.get(token, set()).discard(entry.entry_id or "")

    def exact(self, query: str) -> str | None:
        return self._exact.get(normalize_memory_text(query))

    def candidates(self, query: str) -> List[str]:
        ids: Set[str] = set()
        for token in memory_tokens(query):
            ids.update(self._tokens.get(token, set()))
        return list(ids)

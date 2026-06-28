from __future__ import annotations

import re


class GlossarySelector:
    def __init__(self, glossary: dict):
        self.glossary = glossary or {}

    def select(self, text: str) -> list[dict]:
        matches = []

        for source, item in self.glossary.items():
            if self._contains(text, source):
                matches.append({
                    "source": source,
                    "target": item.get("translation", ""),
                    "category": item.get("category", ""),
                    "locked": item.get("locked", False),
                    "confidence": item.get("confidence", 0),
                    "total_count": item.get("total_count", 0),
                })

        matches.sort(key=lambda x: (-int(bool(x.get("locked"))), -float(x.get("confidence", 0)), x.get("source", "")))
        return matches

    def _contains(self, text: str, source: str) -> bool:
        if not source:
            return False
        if re.fullmatch(r"[A-Za-z0-9_\-]+", source):
            return re.search(rf"\\b{re.escape(source)}\\b", text) is not None
        return source in text

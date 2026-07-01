"""Foundation-08.6 semantic tokenizer.

The tokenizer is deliberately dependency-free so Foundation-08.6 remains
portable on Windows and CI environments. It produces deterministic tokens for
keyword, hybrid, and future semantic backends.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+", re.UNICODE)


@dataclass
class KnowledgeTokenizer:
    """Small normalized tokenizer used by the semantic index."""

    lowercase: bool = True
    min_length: int = 1
    stopwords: set[str] = field(default_factory=set)

    def normalize(self, text: Any) -> str:
        value = "" if text is None else str(text)
        value = value.strip()
        return value.lower() if self.lowercase else value

    def tokenize(self, text: Any) -> List[str]:
        normalized = self.normalize(text)
        raw_tokens = [match.group(0) for match in _TOKEN_RE.finditer(normalized)]
        expanded: List[str] = []
        for token in raw_tokens:
            expanded.append(token)
            # CJK text is often not separated by spaces. Add characters and
            # bigrams so searches like "南國 島嶼" can match "南國島嶼".
            if any("\u4e00" <= char <= "\u9fff" or "\uac00" <= char <= "\ud7af" for char in token) and len(token) > 1:
                expanded.extend(list(token))
                expanded.extend(token[i:i + 2] for i in range(len(token) - 1))
        seen = set()
        tokens: List[str] = []
        for token in expanded:
            if len(token) < self.min_length or token in self.stopwords or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
        return tokens

    def item_tokens(self, item: Any) -> List[str]:
        key = getattr(item, "key", "")
        value = getattr(item, "value", "")
        domain = getattr(item, "domain", "")
        metadata = getattr(item, "metadata", {}) or {}
        metadata_text = " ".join(f"{k} {v}" for k, v in metadata.items())
        return self.tokenize(f"{key} {value} {domain} {metadata_text}")

    def to_dict(self) -> Dict[str, Any]:
        return {"lowercase": self.lowercase, "min_length": self.min_length, "stopwords": sorted(self.stopwords)}


def tokenize(text: Any) -> List[str]:
    return KnowledgeTokenizer().tokenize(text)


__all__ = ["KnowledgeTokenizer", "tokenize"]

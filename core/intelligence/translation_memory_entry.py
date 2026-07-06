# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
import hashlib


def normalize_memory_text(text: str) -> str:
    return " ".join((text or "").strip().split()).lower()


def memory_entry_id(source_text: str, target_text: str) -> str:
    raw = f"{normalize_memory_text(source_text)}\n{normalize_memory_text(target_text)}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


@dataclass(frozen=True)
class TranslationMemoryEntry:
    source_text: str
    target_text: str
    source_language: str = "auto"
    target_language: str = "zh-TW"
    domain: str = "general"
    context_tags: List[str] = field(default_factory=list)
    terminology: Dict[str, str] = field(default_factory=dict)
    character_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_text or not self.source_text.strip():
            raise ValueError("source_text must not be empty")
        if not self.target_text or not self.target_text.strip():
            raise ValueError("target_text must not be empty")
        if self.entry_id is None:
            object.__setattr__(self, "entry_id", memory_entry_id(self.source_text, self.target_text))

    @property
    def normalized_source(self) -> str:
        return normalize_memory_text(self.source_text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "source_text": self.source_text,
            "target_text": self.target_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "domain": self.domain,
            "context_tags": list(self.context_tags),
            "terminology": dict(self.terminology),
            "character_refs": list(self.character_refs),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranslationMemoryEntry":
        return cls(
            source_text=data.get("source_text", ""),
            target_text=data.get("target_text", ""),
            source_language=data.get("source_language", "auto"),
            target_language=data.get("target_language", "zh-TW"),
            domain=data.get("domain", "general"),
            context_tags=list(data.get("context_tags", [])),
            terminology=dict(data.get("terminology", {})),
            character_refs=list(data.get("character_refs", [])),
            metadata=dict(data.get("metadata", {})),
            entry_id=data.get("entry_id"),
        )

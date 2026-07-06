# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .translation_memory_entry import TranslationMemoryEntry


@dataclass(frozen=True)
class TranslationMemoryMatch:
    entry: TranslationMemoryEntry
    score: float
    match_type: str = "fuzzy"
    reasons: List[str] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        return max(0.0, min(1.0, self.score))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
            "confidence": self.confidence,
            "match_type": self.match_type,
            "reasons": list(self.reasons),
        }


@dataclass
class TranslationMemoryResult:
    query: str
    matches: List[TranslationMemoryMatch] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def best_match(self) -> TranslationMemoryMatch | None:
        return self.matches[0] if self.matches else None

    @property
    def has_match(self) -> bool:
        return bool(self.matches)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "matches": [match.to_dict() for match in self.matches],
            "metrics": dict(self.metrics),
        }

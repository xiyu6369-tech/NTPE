# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CharacterMention:
    mention_id: str
    name: str
    canonical_name: str
    segment_id: str | None = None
    mention_type: str = "name"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mention_id": self.mention_id,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "segment_id": self.segment_id,
            "mention_type": self.mention_type,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CharacterFinding:
    category: str
    severity: str
    message: str
    character: str | None = None
    segment_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "character": self.character,
            "segment_id": self.segment_id,
        }


@dataclass
class CharacterIntelligenceResult:
    mentions: List[CharacterMention] = field(default_factory=list)
    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    pronoun_candidates: Dict[str, str] = field(default_factory=dict)
    findings: List[CharacterFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def mention_count(self) -> int:
        return len(self.mentions)

    @property
    def character_count(self) -> int:
        return len(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mentions": [mention.to_dict() for mention in self.mentions],
            "characters": {key: dict(value) for key, value in self.characters.items()},
            "relationships": [dict(item) for item in self.relationships],
            "pronoun_candidates": dict(self.pronoun_candidates),
            "findings": [finding.to_dict() for finding in self.findings],
            "metrics": dict(self.metrics),
        }

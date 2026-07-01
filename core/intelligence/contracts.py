"""NTPE Foundation-07.0 Translation Intelligence Contract.

This module defines stable, dependency-light contracts for translation intelligence.
The contracts are intentionally additive and backward compatible: they do not depend
on existing runtime internals and can be adopted by Context/Prompt/Runtime layers
incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CharacterMemoryEntry:
    source_name: str
    target_name: str
    aliases: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "target_name": self.target_name,
            "aliases": list(self.aliases),
            "traits": list(self.traits),
            "notes": self.notes,
        }


@dataclass
class GlossaryEntry:
    source_term: str
    target_term: str
    category: str = "general"
    locked: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_term": self.source_term,
            "target_term": self.target_term,
            "category": self.category,
            "locked": self.locked,
            "notes": self.notes,
        }


@dataclass
class NarrativeMemoryEntry:
    key: str
    value: str
    scope: str = "global"
    weight: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope,
            "weight": self.weight,
        }


@dataclass
class SceneMemoryEntry:
    scene_id: str
    summary: str
    location: str = ""
    timeline: str = ""
    participants: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "summary": self.summary,
            "location": self.location,
            "timeline": self.timeline,
            "participants": list(self.participants),
        }


@dataclass
class ConsistencyIssue:
    code: str
    message: str
    severity: str = "warning"
    source: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass
class IntelligenceSnapshot:
    characters: List[Dict[str, Any]] = field(default_factory=list)
    glossary: List[Dict[str, Any]] = field(default_factory=list)
    narrative: List[Dict[str, Any]] = field(default_factory=list)
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": list(self.characters),
            "glossary": list(self.glossary),
            "narrative": list(self.narrative),
            "scenes": list(self.scenes),
            "manifest": dict(self.manifest),
        }

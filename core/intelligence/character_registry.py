# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class CharacterRecord:
    canonical_name: str
    localized_name: str | None = None
    original_name: str | None = None
    aliases: List[str] = field(default_factory=list)
    honorifics: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)

    def names(self) -> List[str]:
        values = [self.canonical_name, self.localized_name, self.original_name, *self.aliases, *self.honorifics]
        return [value for value in values if value]

    def to_dict(self) -> Dict[str, object]:
        return {
            "canonical_name": self.canonical_name,
            "localized_name": self.localized_name,
            "original_name": self.original_name,
            "aliases": list(self.aliases),
            "honorifics": list(self.honorifics),
            "metadata": dict(self.metadata),
        }


class CharacterRegistry:
    """Canonical character registry with alias lookup."""

    def __init__(self) -> None:
        self._records: Dict[str, CharacterRecord] = {}
        self._alias_index: Dict[str, str] = {}

    def register(
        self,
        canonical_name: str,
        *,
        localized_name: str | None = None,
        original_name: str | None = None,
        aliases: Iterable[str] | None = None,
        honorifics: Iterable[str] | None = None,
        **metadata: object,
    ) -> CharacterRecord:
        record = CharacterRecord(
            canonical_name=canonical_name,
            localized_name=localized_name,
            original_name=original_name,
            aliases=list(aliases or []),
            honorifics=list(honorifics or []),
            metadata=dict(metadata),
        )
        self._records[canonical_name] = record
        for name in record.names():
            self._alias_index[name] = canonical_name
        return record

    def resolve(self, name: str) -> str | None:
        return self._alias_index.get(name)

    def get(self, canonical_name: str) -> CharacterRecord | None:
        return self._records.get(canonical_name)

    def all(self) -> List[CharacterRecord]:
        return list(self._records.values())

    def to_dict(self) -> Dict[str, Dict[str, object]]:
        return {key: value.to_dict() for key, value in self._records.items()}

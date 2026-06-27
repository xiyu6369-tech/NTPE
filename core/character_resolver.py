# =====================================================
# NTPE Character Resolver v1.1.1
# 功能：
# 1. 建立人名全名 / 名 / 姓別名索引
# 2. 最長匹配優先
# 3. 可由 glossary.json / glossary_override.json 產生角色別名
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional
import re


@dataclass
class CharacterEntry:
    source_full: str
    target_full: str
    source_parts: List[str] = field(default_factory=list)
    target_parts: List[str] = field(default_factory=list)
    aliases: Dict[str, str] = field(default_factory=dict)
    category: str = "person_name"
    locked: bool = True
    confidence: float = 1.0

    def to_alias_map(self) -> Dict[str, str]:
        result: Dict[str, str] = {}

        if self.source_full and self.target_full:
            result[self.source_full] = self.target_full

        if len(self.source_parts) == len(self.target_parts):
            for source, target in zip(self.source_parts, self.target_parts):
                if source and target:
                    result[source] = target

        for source, target in self.aliases.items():
            source = str(source).strip()
            target = str(target).strip()
            if source and target:
                result[source] = target

        return result

    def to_dict(self) -> dict:
        return {
            "source_full": self.source_full,
            "target_full": self.target_full,
            "source_parts": self.source_parts,
            "target_parts": self.target_parts,
            "aliases": self.aliases,
            "category": self.category,
            "locked": self.locked,
            "confidence": self.confidence,
        }


class CharacterResolver:
    def __init__(self) -> None:
        self.characters: List[CharacterEntry] = []
        self.alias_map: Dict[str, str] = {}
        self.collisions: Dict[str, List[str]] = {}

    def add_character(
        self,
        source_full: str,
        target_full: str,
        source_parts: Optional[List[str]] = None,
        target_parts: Optional[List[str]] = None,
        aliases: Optional[Dict[str, str]] = None,
        category: str = "person_name",
        locked: bool = True,
        confidence: float = 1.0,
    ) -> None:
        source_full = str(source_full).strip()
        target_full = str(target_full).strip()

        if not source_full or not target_full:
            return

        if source_parts is None:
            source_parts = self.split_source_name(source_full)
        if target_parts is None:
            target_parts = self.split_target_name(target_full)

        entry = CharacterEntry(
            source_full=source_full,
            target_full=target_full,
            source_parts=source_parts,
            target_parts=target_parts,
            aliases=aliases or {},
            category=category,
            locked=locked,
            confidence=confidence,
        )
        self.characters.append(entry)
        self.rebuild_alias_map()

    def load_from_glossary_terms(self, glossary_terms: Dict[str, dict]) -> None:
        for source, item in glossary_terms.items():
            if not isinstance(item, dict):
                continue

            target = str(item.get("translation", "")).strip()
            if not target:
                continue

            category = str(item.get("category", "")).strip()
            locked = bool(item.get("locked", False))
            confidence = float(item.get("confidence", 0.0) or 0.0)

            if not self.looks_like_person_name(source, category=category):
                continue

            alias_dict: Dict[str, str] = {}
            raw_aliases = item.get("aliases", [])
            if isinstance(raw_aliases, list):
                target_parts = self.split_target_name(target)
                for alias in raw_aliases:
                    alias = str(alias).strip()
                    if not alias:
                        continue
                    alias_parts = self.split_source_name(alias)
                    if len(alias_parts) == len(target_parts):
                        for src, dst in zip(alias_parts, target_parts):
                            alias_dict[src] = dst
                    else:
                        alias_dict[alias] = target

            self.add_character(
                source_full=str(source),
                target_full=target,
                aliases=alias_dict,
                category=category or "person_name",
                locked=locked,
                confidence=confidence,
            )

    def rebuild_alias_map(self) -> None:
        alias_map: Dict[str, str] = {}
        collisions: Dict[str, List[str]] = {}

        for char in self.characters:
            for source, target in char.to_alias_map().items():
                if source in alias_map and alias_map[source] != target:
                    collisions.setdefault(source, [alias_map[source]])
                    if target not in collisions[source]:
                        collisions[source].append(target)
                    continue
                alias_map[source] = target

        self.alias_map = dict(sorted(alias_map.items(), key=lambda kv: len(kv[0]), reverse=True))
        self.collisions = collisions

    def resolve(self, text: str) -> str:
        if not text:
            return text

        result = text
        for source, target in self.alias_map.items():
            if source == target:
                continue
            result = result.replace(source, target)
        return result

    def export_alias_index(self) -> dict:
        return {
            "version": "1.1.1",
            "character_count": len(self.characters),
            "alias_count": len(self.alias_map),
            "aliases": self.alias_map,
            "collisions": self.collisions,
            "characters": [entry.to_dict() for entry in self.characters],
        }

    @staticmethod
    def split_source_name(name: str) -> List[str]:
        name = str(name).strip()
        if not name:
            return []
        if " " in name:
            return [part.strip() for part in name.split() if part.strip()]
        if "・" in name:
            return [part.strip() for part in name.split("・") if part.strip()]
        return [name]

    @staticmethod
    def split_target_name(name: str) -> List[str]:
        name = str(name).strip()
        if not name:
            return []
        if "・" in name:
            return [part.strip() for part in name.split("・") if part.strip()]
        if " " in name:
            return [part.strip() for part in name.split() if part.strip()]
        return [name]

    @staticmethod
    def looks_like_person_name(source: str, category: str = "") -> bool:
        source = str(source).strip()
        category = str(category).strip().lower()

        if not source:
            return False

        if category in {
            "person",
            "person_name",
            "character",
            "character_name",
            "name",
            "proper_name",
        }:
            return True

        if re.search(r"[가-힣]+\s+[가-힣]+", source):
            return True
        if re.search(r"[A-Za-z]+\s+[A-Za-z]+", source):
            return True

        return False

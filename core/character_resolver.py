# =====================================================
# NTPE 1.1.2 Character Resolver
# 功能：
# 1. 人名全名 / 名 / 姓別名解析
# 2. Longest Match 最長匹配
# 3. Alias Priority 別名優先級
# 4. Collision Guard 碰撞保護
# 5. Regex Safe Replace 安全替換
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import json
import re


class AliasPriority(IntEnum):
    SURNAME = 10
    GIVEN_NAME = 20
    ALIAS = 30
    FULL_NAME = 100
    MANUAL_LOCKED = 200


@dataclass(frozen=True)
class AliasEntry:
    source: str
    target: str
    priority: int = int(AliasPriority.ALIAS)
    owner: str = ""
    kind: str = "alias"
    locked: bool = False

    @property
    def length(self) -> int:
        return len(self.source)


@dataclass
class CollisionReport:
    accepted: List[AliasEntry] = field(default_factory=list)
    rejected: List[dict] = field(default_factory=list)
    warnings: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "accepted": [entry.__dict__ for entry in self.accepted],
            "rejected": self.rejected,
            "warnings": self.warnings,
        }


class CharacterResolver:
    RESERVED_ALIAS = {
        "先生", "小姐", "夫人", "老師", "醫生", "哥哥", "姐姐", "弟弟", "妹妹",
        "doctor", "teacher", "king", "queen", "sir", "madam", "brother", "sister",
        "그", "그녀", "남자", "여자", "형", "오빠", "누나", "언니", "선생", "의사",
    }

    def __init__(self) -> None:
        self._entries: Dict[str, AliasEntry] = {}
        self.report = CollisionReport()

    def add_character(
        self,
        source_full: str,
        target_full: str,
        source_parts: Optional[List[str]] = None,
        target_parts: Optional[List[str]] = None,
        locked: bool = True,
    ) -> None:
        source_full = self._normalize(source_full)
        target_full = self._normalize(target_full)
        if not source_full or not target_full:
            return

        owner = source_full
        self.add_alias(
            source_full,
            target_full,
            priority=AliasPriority.MANUAL_LOCKED if locked else AliasPriority.FULL_NAME,
            owner=owner,
            kind="full_name",
            locked=locked,
        )

        source_parts = source_parts or self._split_source_name(source_full)
        target_parts = target_parts or self._split_target_name(target_full)

        if len(source_parts) == len(target_parts) and len(source_parts) >= 2:
            for index, (src, tgt) in enumerate(zip(source_parts, target_parts)):
                kind = "given_name" if index == 0 else "surname"
                priority = AliasPriority.GIVEN_NAME if index == 0 else AliasPriority.SURNAME
                self.add_alias(src, tgt, priority=priority, owner=owner, kind=kind, locked=False)

    def add_alias(
        self,
        source: str,
        target: str,
        priority: int | AliasPriority = AliasPriority.ALIAS,
        owner: str = "",
        kind: str = "alias",
        locked: bool = False,
    ) -> bool:
        source = self._normalize(source)
        target = self._normalize(target)
        owner = self._normalize(owner)

        if not source or not target:
            return False
        if source == target:
            return False
        if self._is_reserved(source):
            self.report.rejected.append({
                "source": source,
                "target": target,
                "reason": "reserved_alias",
                "kind": kind,
                "owner": owner,
            })
            return False

        entry = AliasEntry(
            source=source,
            target=target,
            priority=int(priority),
            owner=owner,
            kind=kind,
            locked=bool(locked),
        )

        old = self._entries.get(source)
        if old is None:
            self._entries[source] = entry
            self.report.accepted.append(entry)
            return True

        if old.target == target:
            if entry.priority > old.priority:
                self._entries[source] = entry
            return True

        winner = self._pick_collision_winner(old, entry)
        loser = entry if winner is old else old
        self._entries[source] = winner
        self.report.rejected.append({
            "source": source,
            "rejected_target": loser.target,
            "kept_target": winner.target,
            "reason": "alias_collision_lower_priority",
            "rejected_owner": loser.owner,
            "kept_owner": winner.owner,
        })
        return winner is entry

    def load_from_glossary(self, glossary: dict) -> None:
        terms = glossary.get("terms", glossary) if isinstance(glossary, dict) else {}
        if not isinstance(terms, dict):
            return

        for source, item in terms.items():
            if isinstance(item, str):
                translation = item
                locked = True
                aliases: List[str] = []
            elif isinstance(item, dict):
                translation = item.get("translation", "")
                locked = bool(item.get("locked", False))
                aliases = item.get("aliases", []) if isinstance(item.get("aliases", []), list) else []
            else:
                continue

            source = self._normalize(source)
            translation = self._normalize(translation)
            if not source or not translation:
                continue
            if not self._looks_like_person_name(source):
                continue

            self.add_character(source, translation, locked=locked)
            for alias in aliases:
                alias = self._normalize(alias)
                if alias:
                    self.add_alias(alias, translation, priority=AliasPriority.ALIAS, owner=source, kind="manual_alias", locked=locked)

    def resolve(self, text: str) -> str:
        if not text:
            return text
        result = text
        for entry in self._ordered_entries():
            result = self._safe_replace(result, entry.source, entry.target)
        return result

    def export_alias_index(self) -> dict:
        return {
            "version": "1.1.2",
            "rules": {
                "longest_match": True,
                "collision_guard": True,
                "regex_safe_replace": True,
                "priority_order": "manual_locked > full_name > alias > given_name > surname",
            },
            "aliases": [entry.__dict__ for entry in self._ordered_entries()],
            "collision_report": self.report.to_dict(),
        }

    def save_alias_index(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.export_alias_index(), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_alias_map(self) -> Dict[str, str]:
        return {entry.source: entry.target for entry in self._ordered_entries()}

    def _ordered_entries(self) -> List[AliasEntry]:
        return sorted(
            self._entries.values(),
            key=lambda e: (e.length, e.priority, e.locked, e.source),
            reverse=True,
        )

    def _pick_collision_winner(self, old: AliasEntry, new: AliasEntry) -> AliasEntry:
        old_key = (old.locked, old.priority, old.length)
        new_key = (new.locked, new.priority, new.length)
        return new if new_key > old_key else old

    def _safe_replace(self, text: str, source: str, target: str) -> str:
        if not source or source == target:
            return text

        if self._contains_latin(source):
            pattern = rf"(?<![A-Za-z0-9_]){re.escape(source)}(?![A-Za-z0-9_])"
            return re.sub(pattern, target, text)

        return text.replace(source, target)

    def _split_source_name(self, name: str) -> List[str]:
        name = self._normalize(name)
        if " " in name:
            return [p for p in name.split(" ") if p]
        if "・" in name:
            return [p for p in name.split("・") if p]
        return [name]

    def _split_target_name(self, name: str) -> List[str]:
        name = self._normalize(name)
        if "・" in name:
            return [p for p in name.split("・") if p]
        if " " in name:
            return [p for p in name.split(" ") if p]
        return [name]

    def _looks_like_person_name(self, source: str) -> bool:
        source = self._normalize(source)
        if not source or self._is_reserved(source):
            return False
        if re.search(r"[가-힣]+\s+[가-힣]+", source):
            return True
        if re.search(r"[A-Za-z]+\s+[A-Za-z]+", source):
            return True
        if "・" in source:
            return True
        return False

    def _is_reserved(self, source: str) -> bool:
        return self._normalize(source).lower() in {x.lower() for x in self.RESERVED_ALIAS}

    def _contains_latin(self, text: str) -> bool:
        return bool(re.search(r"[A-Za-z]", text))

    def _normalize(self, value: object) -> str:
        text = str(value or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text


def build_alias_index_from_glossary(glossary: dict, output_path: str | Path | None = None) -> dict:
    resolver = CharacterResolver()
    resolver.load_from_glossary(glossary)
    index = resolver.export_alias_index()
    if output_path is not None:
        resolver.save_alias_index(output_path)
    return index

# =====================================================
# NTPE Character Resolver v1.1.0
# 功能：
# 1. 人名全名 / 名字 / 姓氏別名解析
# 2. 最長匹配優先，避免短名破壞全名
# 3. 支援 glossary.json、glossary_only.json、character_database.json、character_match_dictionary.json
# 4. 不直接覆蓋既有 Glossary / Character Database 功能，可被後續版本整合
# =====================================================

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"


@dataclass
class CharacterAlias:
    source: str
    target: str
    alias_type: str = "alias"
    priority: int = 50
    locked: bool = False
    character_id: str = ""

    def normalized(self) -> Optional["CharacterAlias"]:
        source = normalize_token(self.source)
        target = str(self.target or "").strip()
        if not source or not target or source == target:
            return None
        return CharacterAlias(
            source=source,
            target=target,
            alias_type=self.alias_type or "alias",
            priority=int(self.priority or 50),
            locked=bool(self.locked),
            character_id=self.character_id or "",
        )


@dataclass
class CharacterEntry:
    source_full: str
    target_full: str
    character_id: str = ""
    locked: bool = False
    aliases: List[CharacterAlias] = field(default_factory=list)

    def build_aliases(self) -> List[CharacterAlias]:
        result: List[CharacterAlias] = []

        source_full = normalize_token(self.source_full)
        target_full = str(self.target_full or "").strip()

        if source_full and target_full:
            result.append(
                CharacterAlias(
                    source=source_full,
                    target=target_full,
                    alias_type="fullname",
                    priority=120,
                    locked=self.locked,
                    character_id=self.character_id,
                )
            )

            source_parts = split_name_parts(source_full)
            target_parts = split_name_parts(target_full)

            if len(source_parts) == len(target_parts) and len(source_parts) > 1:
                for index, (src, tgt) in enumerate(zip(source_parts, target_parts)):
                    alias_type = "firstname" if index == 0 else "lastname"
                    priority = 80 if index == 0 else 70
                    result.append(
                        CharacterAlias(
                            source=src,
                            target=tgt,
                            alias_type=alias_type,
                            priority=priority,
                            locked=self.locked,
                            character_id=self.character_id,
                        )
                    )

        result.extend(self.aliases)
        return [alias for alias in (a.normalized() for a in result) if alias is not None]


class CharacterResolver:
    def __init__(self) -> None:
        self.alias_map: Dict[str, CharacterAlias] = {}
        self.collision_log: List[Dict[str, Any]] = []

    def add_alias(
        self,
        source: str,
        target: str,
        alias_type: str = "alias",
        priority: int = 50,
        locked: bool = False,
        character_id: str = "",
    ) -> None:
        alias = CharacterAlias(
            source=source,
            target=target,
            alias_type=alias_type,
            priority=priority,
            locked=locked,
            character_id=character_id,
        ).normalized()
        if alias is None:
            return

        old = self.alias_map.get(alias.source)
        if old is None:
            self.alias_map[alias.source] = alias
            return

        if should_replace_alias(old, alias):
            self.collision_log.append(
                {
                    "source": alias.source,
                    "old_target": old.target,
                    "new_target": alias.target,
                    "reason": "higher_priority_or_locked",
                }
            )
            self.alias_map[alias.source] = alias
        elif old.target != alias.target:
            self.collision_log.append(
                {
                    "source": alias.source,
                    "old_target": old.target,
                    "new_target": alias.target,
                    "reason": "kept_existing_alias",
                }
            )

    def add_character(
        self,
        source_full: str,
        target_full: str,
        character_id: str = "",
        locked: bool = False,
        aliases: Optional[Iterable[CharacterAlias]] = None,
    ) -> None:
        entry = CharacterEntry(
            source_full=source_full,
            target_full=target_full,
            character_id=character_id,
            locked=locked,
            aliases=list(aliases or []),
        )
        for alias in entry.build_aliases():
            self.add_alias(
                alias.source,
                alias.target,
                alias.alias_type,
                alias.priority,
                alias.locked,
                alias.character_id,
            )

    def load_from_glossary(self, glossary_data: Dict[str, Any]) -> None:
        terms = glossary_data.get("terms", glossary_data)
        if not isinstance(terms, dict):
            return

        for source, item in terms.items():
            if isinstance(item, str):
                target = item
                locked = True
                aliases = []
                category = "manual"
            elif isinstance(item, dict):
                target = item.get("translation", "")
                locked = bool(item.get("locked", False))
                aliases = item.get("aliases", []) if isinstance(item.get("aliases", []), list) else []
                category = str(item.get("category", ""))
            else:
                continue

            if not target or not looks_like_name(source, category):
                continue

            self.add_character(str(source), str(target), locked=locked)
            for alias in aliases:
                if isinstance(alias, str):
                    self.add_alias(alias, target, "glossary_alias", 65, locked)
                elif isinstance(alias, dict):
                    self.add_alias(
                        alias.get("source", ""),
                        alias.get("target", target),
                        alias.get("type", "glossary_alias"),
                        int(alias.get("priority", 65) or 65),
                        locked,
                    )

    def load_from_character_database(self, database_data: Dict[str, Any]) -> None:
        match_dictionary = database_data.get("match_dictionary")
        if isinstance(match_dictionary, dict):
            self.load_from_match_dictionary(match_dictionary)
            return

        characters = database_data.get("characters", [])
        if not isinstance(characters, list):
            return

        for char in characters:
            if not isinstance(char, dict):
                continue
            cid = str(char.get("character_id", ""))
            locked = bool(char.get("locked", False))
            fullname = char.get("fullname", {}) if isinstance(char.get("fullname", {}), dict) else {}
            single = char.get("single_name", {}) if isinstance(char.get("single_name", {}), dict) else {}
            first = char.get("firstname", {}) if isinstance(char.get("firstname", {}), dict) else {}
            last = char.get("lastname", {}) if isinstance(char.get("lastname", {}), dict) else {}

            target_full = fullname.get("zh_tw") or single.get("zh_tw") or ""
            for source, target, alias_type, priority in [
                (fullname.get("ko", ""), target_full, "fullname_ko", 120),
                (fullname.get("en", ""), target_full, "fullname_en", 110),
                (single.get("ko", ""), single.get("zh_tw", target_full), "single_name_ko", 90),
                (single.get("en", ""), single.get("zh_tw", target_full), "single_name_en", 80),
                (first.get("ko", ""), first.get("zh_tw", ""), "firstname_ko", 70),
                (first.get("en", ""), first.get("zh_tw", ""), "firstname_en", 65),
                (last.get("ko", ""), last.get("zh_tw", ""), "lastname_ko", 60),
                (last.get("en", ""), last.get("zh_tw", ""), "lastname_en", 55),
            ]:
                self.add_alias(str(source), str(target), alias_type, priority, locked, cid)

            aliases = char.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    if isinstance(alias, dict):
                        self.add_alias(
                            alias.get("source", ""),
                            alias.get("target", target_full),
                            alias.get("type", "alias"),
                            int(alias.get("priority", 50) or 50),
                            locked,
                            cid,
                        )
                    elif isinstance(alias, str):
                        self.add_alias(alias, target_full, "alias", 50, locked, cid)

    def load_from_match_dictionary(self, match_dictionary: Dict[str, Any]) -> None:
        for source, item in match_dictionary.items():
            if isinstance(item, str):
                self.add_alias(source, item, "match_dictionary", 75, True)
            elif isinstance(item, dict):
                self.add_alias(
                    source,
                    item.get("target", ""),
                    item.get("match_type", "match_dictionary"),
                    int(item.get("priority", 75) or 75),
                    bool(item.get("locked", False)),
                    item.get("character_id", ""),
                )

    def resolve(self, text: str) -> str:
        if not text or not self.alias_map:
            return text

        result = text
        for source, alias in sorted(
            self.alias_map.items(),
            key=lambda kv: (-kv[1].priority, -len(kv[0]), kv[0]),
        ):
            result = safe_replace(result, source, alias.target)
        return result

    def export_match_dictionary(self) -> Dict[str, Dict[str, Any]]:
        return {
            source: {
                "source": alias.source,
                "target": alias.target,
                "match_type": alias.alias_type,
                "priority": alias.priority,
                "locked": alias.locked,
                "character_id": alias.character_id,
            }
            for source, alias in sorted(
                self.alias_map.items(),
                key=lambda kv: (-kv[1].priority, -len(kv[0]), kv[0]),
            )
        }

    def save_match_dictionary(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.export_match_dictionary(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def normalize_token(token: str) -> str:
    token = str(token or "").strip()
    token = re.sub(r"\s+", " ", token)
    return token


def split_name_parts(name: str) -> List[str]:
    name = normalize_token(name)
    if not name:
        return []
    if "・" in name:
        return [p.strip() for p in name.split("・") if p.strip()]
    if " " in name:
        return [p.strip() for p in name.split(" ") if p.strip()]
    return [name]


def looks_like_name(source: str, category: str = "") -> bool:
    source = normalize_token(source)
    category = str(category or "").lower()
    if not source:
        return False
    if "name" in category or "person" in category or "character" in category:
        return True
    if re.search(r"[가-힣]+\s+[가-힣]+", source):
        return True
    if re.search(r"[A-Z][A-Za-z'\-]+\s+[A-Z][A-Za-z'\-]+", source):
        return True
    return False


def should_replace_alias(old: CharacterAlias, new: CharacterAlias) -> bool:
    if new.locked and not old.locked:
        return True
    if new.locked == old.locked and new.priority > old.priority:
        return True
    if new.locked == old.locked and new.priority == old.priority:
        return len(new.source) > len(old.source)
    return False


def safe_replace(text: str, source: str, target: str) -> str:
    if not source or source == target:
        return text

    # 英文 / 數字詞避免替換到單字中間；韓文、中文保留直接替換。
    if re.fullmatch(r"[A-Za-z0-9 .'-]+", source):
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(source)}(?![A-Za-z0-9_])")
        return pattern.sub(target, text)

    return text.replace(source, target)


def load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def build_default_resolver(memory_dir: Path = MEMORY_DIR) -> CharacterResolver:
    resolver = CharacterResolver()

    for file_name, loader in [
        ("character_match_dictionary.json", resolver.load_from_match_dictionary),
        ("character_database.json", resolver.load_from_character_database),
        ("glossary.json", resolver.load_from_glossary),
        ("glossary_only.json", resolver.load_from_glossary),
    ]:
        data = load_json_file(memory_dir / file_name)
        if data:
            loader(data)

    return resolver


__all__ = [
    "CharacterAlias",
    "CharacterEntry",
    "CharacterResolver",
    "build_default_resolver",
    "looks_like_name",
    "split_name_parts",
]

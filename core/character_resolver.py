# =====================================================
# NTPE 1.1.0 Character Resolver
# 人名解析器
# =====================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class CharacterEntry:
    source_full: str
    target_full: str
    source_parts: List[str] = field(default_factory=list)
    target_parts: List[str] = field(default_factory=list)

    def aliases(self) -> Dict[str, str]:
        result: Dict[str, str] = {}

        if self.source_full and self.target_full:
            result[self.source_full] = self.target_full

        if len(self.source_parts) == len(self.target_parts):
            for source, target in zip(self.source_parts, self.target_parts):
                source = source.strip()
                target = target.strip()
                if source and target:
                    result[source] = target

        return result


class CharacterResolver:
    """
    NTPE Character Resolver

    目的：
    1. 全名翻全名。
    2. 名字翻名字。
    3. 姓氏翻姓氏。
    4. 最長匹配優先，避免短名稱破壞全名。
    """

    def __init__(self):
        self.characters: List[CharacterEntry] = []
        self.alias_map: Dict[str, str] = {}

    def add_character(
        self,
        source_full: str,
        target_full: str,
        source_parts: Optional[List[str]] = None,
        target_parts: Optional[List[str]] = None,
    ) -> None:
        source_full = source_full.strip()
        target_full = target_full.strip()

        if not source_full or not target_full:
            return

        if source_parts is None:
            source_parts = self._split_source_name(source_full)

        if target_parts is None:
            target_parts = self._split_target_name(target_full)

        entry = CharacterEntry(
            source_full=source_full,
            target_full=target_full,
            source_parts=source_parts,
            target_parts=target_parts,
        )

        self.characters.append(entry)
        self._rebuild_alias_map()

    def load_from_glossary_dict(self, glossary: Dict[str, str]) -> None:
        for source, target in glossary.items():
            if self._looks_like_person_name(source):
                self.add_character(source, target)

    def resolve(self, text: str) -> str:
        if not text:
            return text

        result = text

        # 最長優先，避免「일라이」先替換後破壞「일라이 리그로우」
        for source in sorted(self.alias_map.keys(), key=len, reverse=True):
            target = self.alias_map[source]
            result = self._safe_replace(result, source, target)

        return result

    def get_alias_map(self) -> Dict[str, str]:
        return dict(self.alias_map)

    def _rebuild_alias_map(self) -> None:
        alias_map: Dict[str, str] = {}

        for character in self.characters:
            for source, target in character.aliases().items():
                alias_map[source] = target

        self.alias_map = alias_map

    def _split_source_name(self, name: str) -> List[str]:
        name = name.strip()

        if " " in name:
            return [part.strip() for part in name.split() if part.strip()]

        if "・" in name:
            return [part.strip() for part in name.split("・") if part.strip()]

        return [name]

    def _split_target_name(self, name: str) -> List[str]:
        name = name.strip()

        if "・" in name:
            return [part.strip() for part in name.split("・") if part.strip()]

        if " " in name:
            return [part.strip() for part in name.split() if part.strip()]

        return [name]

    def _looks_like_person_name(self, source: str) -> bool:
        source = source.strip()

        if not source:
            return False

        if re.search(r"[가-힣]+\s+[가-힣]+", source):
            return True

        if re.search(r"[A-Za-z]+\s+[A-Za-z]+", source):
            return True

        if re.search(r"[가-힣]", source):
            return True

        return False

    def _safe_replace(self, text: str, source: str, target: str) -> str:
        if source == target:
            return text

        return text.replace(source, target)

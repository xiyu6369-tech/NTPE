from __future__ import annotations

from .utils import regex_search


class CharacterSelector:
    def __init__(self, match_dictionary: dict):
        self.match_dictionary = match_dictionary or {}

    def select(self, text: str) -> list[dict]:
        matches = []

        for source, item in self.match_dictionary.items():
            pattern = item.get("regex", "")
            if pattern and regex_search(pattern, text):
                matches.append({
                    "source": source,
                    "target": item.get("target", ""),
                    "character_id": item.get("character_id", ""),
                    "match_type": item.get("match_type", ""),
                    "priority": item.get("priority", 0),
                    "locked": item.get("locked", False),
                    "regex": pattern,
                    "rule": self._rule_text(item.get("match_type", "")),
                })

        matches.sort(key=lambda x: (-int(x.get("priority", 0)), -len(x.get("source", "")), x.get("source", "")))

        seen = set()
        result = []
        for m in matches:
            if m["source"] in seen:
                continue
            seen.add(m["source"])
            result.append(m)

        return result

    def _rule_text(self, match_type: str) -> str:
        if match_type.startswith("fullname"):
            return "全名翻全名"
        if match_type.startswith("firstname"):
            return "名字翻名字，不可擴展為全名"
        if match_type.startswith("lastname"):
            return "姓氏翻姓氏，不可擴展為全名"
        if match_type.startswith("single_name"):
            return "單名或韓文無空格姓名不拆"
        return "依角色資料庫指定譯名"

from __future__ import annotations

import re

from .utils import regex_search


class CharacterSelector:
    """
    Prompt Builder Character Selector v1.0.1 Hotfix

    修正：
    - v1.0 直接使用 Character Database regex，遇到韓文助詞會失敗。
      例如：
        일라이 + 가  -> 일라이가
        정태의 + 는  -> 정태의는

    v1.0.1：
    - 仍優先使用 Character Database regex。
    - 若未命中，對韓文 source 啟用「韓文助詞安全匹配」。
    - 不改 Character Database，本修正只影響 Prompt Builder 的選取行為。
    """

    KOREAN_PARTICLES = (
        "가", "이", "은", "는", "을", "를", "에", "에서", "에게", "한테",
        "께", "도", "만", "부터", "까지", "와", "과", "랑", "하고", "로", "으로",
        "의", "야", "아", "여", "이라", "라", "이라고", "라고", "처럼", "보다",
    )

    def __init__(self, match_dictionary: dict):
        self.match_dictionary = match_dictionary or {}

    def select(self, text: str) -> list[dict]:
        matches = []

        for source, item in self.match_dictionary.items():
            pattern = item.get("regex", "")
            matched = False

            if pattern and regex_search(pattern, text):
                matched = True

            if not matched and self._is_korean_source(source):
                matched = self._match_korean_with_particle(text, source)

            if matched:
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

        matches.sort(
            key=lambda x: (
                -int(x.get("priority", 0)),
                -len(x.get("source", "")),
                x.get("source", ""),
            )
        )

        return self._dedupe(matches)

    def _dedupe(self, matches: list[dict]) -> list[dict]:
        seen_sources = set()
        result = []

        for m in matches:
            src = m["source"]
            if src in seen_sources:
                continue
            seen_sources.add(src)
            result.append(m)

        return result

    def _is_korean_source(self, source: str) -> bool:
        return bool(re.fullmatch(r"[가-힣 ]+", source or ""))

    def _match_korean_with_particle(self, text: str, source: str) -> bool:
        """
        韓文安全匹配：
        - source 前面不可接韓文字母，避免匹配到詞中間。
        - source 後面可以是：
          1. 字串結尾
          2. 非韓文字母
          3. 常見韓文助詞
        """
        escaped = re.escape(source)

        particle_group = "|".join(sorted(
            (re.escape(p) for p in self.KOREAN_PARTICLES),
            key=len,
            reverse=True,
        ))

        pattern = rf"(?<![가-힣]){escaped}(?:{particle_group})?(?![가-힣])"

        return re.search(pattern, text) is not None

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

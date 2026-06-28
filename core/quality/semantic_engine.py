from __future__ import annotations

import json
import re
from pathlib import Path


class SemanticTranslationEngine:
    """
    TQF-02 Semantic Translation Engine

    用途：
    - 讀取 rules/semantic_translation_rules.json
    - 掃描目前 chunk 是否出現高風險語義詞
    - 回傳 semantic_matches 給 Prompt Builder
    - 讓模型翻譯前知道「必須譯成什麼」與「不能譯成什麼」

    注意：
    這不是 Glossary。Glossary 管專有名詞；Semantic Engine 管容易誤譯、摘要化或幻覺的語義點。
    """

    KOREAN_PARTICLES = (
        "가", "이", "은", "는", "을", "를", "에", "에서", "에게", "한테",
        "께", "도", "만", "부터", "까지", "와", "과", "랑", "하고", "로", "으로",
        "의", "야", "아", "여", "이라", "라", "이라고", "라고", "처럼", "보다",
    )

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = self.root / "rules" / "semantic_translation_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict]:
        if not self.rules_path.exists():
            return []

        data = json.loads(self.rules_path.read_text(encoding="utf-8-sig"))
        rules = data.get("rules", [])

        return [r for r in rules if isinstance(r, dict) and r.get("source")]

    def select(self, text: str) -> list[dict]:
        matches = []

        for rule in self.rules:
            source = str(rule.get("source", "")).strip()
            if not source:
                continue

            if self._contains_source(text, source):
                matches.append({
                    "source": source,
                    "preferred": rule.get("preferred", ""),
                    "required": rule.get("required", []),
                    "allowed": rule.get("allowed", []),
                    "forbidden": rule.get("forbidden", []),
                    "level": rule.get("level", "B"),
                    "category": rule.get("category", "semantic"),
                    "note": rule.get("note", ""),
                })

        level_rank = {"A": 0, "B": 1, "C": 2}
        matches.sort(key=lambda x: (level_rank.get(x.get("level", "B"), 1), x.get("source", "")))
        return matches

    def build_semantic_dictionary(self, matches: list[dict]) -> dict:
        result = {}
        for item in matches:
            preferred = item.get("preferred", "")
            if preferred:
                result[item["source"]] = preferred
            elif item.get("required"):
                result[item["source"]] = item["required"][0]
        return result

    def build_prompt_rules(self, matches: list[dict]) -> list[str]:
        rules = []

        for item in matches:
            source = item["source"]
            preferred = item.get("preferred", "")
            required = item.get("required", [])
            forbidden = item.get("forbidden", [])

            if preferred:
                rules.append(f"{source} 必須依語境譯為「{preferred}」。")
            elif required:
                rules.append(f"{source} 的譯文必須包含：{'／'.join(required)}。")

            if forbidden:
                rules.append(f"{source} 禁止譯成：{'／'.join(forbidden)}。")

            note = item.get("note", "")
            if note:
                rules.append(f"{source} 語義提醒：{note}")

        return rules

    def _contains_source(self, text: str, source: str) -> bool:
        if source in text:
            return True

        if re.fullmatch(r"[가-힣 ]+", source):
            return self._match_korean_with_particle(text, source)

        return False

    def _match_korean_with_particle(self, text: str, source: str) -> bool:
        escaped = re.escape(source)
        particle_group = "|".join(sorted((re.escape(p) for p in self.KOREAN_PARTICLES), key=len, reverse=True))
        pattern = rf"(?<![가-힣]){escaped}(?:{particle_group})?(?![가-힣])"
        return re.search(pattern, text) is not None

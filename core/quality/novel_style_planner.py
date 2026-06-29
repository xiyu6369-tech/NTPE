from __future__ import annotations

import json
from pathlib import Path


class NovelStylePlanner:
    """
    TQF-05.1 Novel Style Planner

    用途：
    - 不翻譯、不修文。
    - 根據目前 chunk 的內容，產生「出版級小說翻譯策略」。
    - 提供給 Prompt Builder，讓模型在翻譯前就知道本段需要保留哪些敘事重點。

    與 Coverage QA 的差異：
    - Coverage QA 是翻譯後檢查是否漏翻。
    - Novel Style Planner 是翻譯前規劃如何避免摘要化、機翻腔與畫面流失。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = self.root / "rules" / "novel_style_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        if not self.rules_path.exists():
            return {
                "style_profile": {"principles": []},
                "expansion_rules": [],
                "forbidden_style": [],
                "preferred_style_examples": [],
            }

        return json.loads(self.rules_path.read_text(encoding="utf-8-sig"))

    def plan(self, text: str) -> dict:
        text = text or ""

        principles = self.rules.get("style_profile", {}).get("principles", [])
        matched_rules = []

        for rule in self.rules.get("expansion_rules", []):
            keywords = rule.get("trigger_keywords", [])
            if any(k and k in text for k in keywords):
                matched_rules.append({
                    "id": rule.get("id", ""),
                    "instruction": rule.get("instruction", ""),
                    "matched_keywords": [k for k in keywords if k and k in text],
                })

        # 如果沒有命中，也提供基礎小說風格規劃。
        if not matched_rules:
            matched_rules.append({
                "id": "BASE_NOVEL_STYLE",
                "instruction": "以台灣繁體中文出版小說語感完整翻譯，避免摘要化與機翻句式。",
                "matched_keywords": [],
            })

        return {
            "style_target": self.rules.get("style_profile", {}).get("target", "台灣繁體中文出版級小說譯文"),
            "principles": principles,
            "matched_rules": matched_rules,
            "forbidden_style": self.rules.get("forbidden_style", []),
            "preferred_style_examples": self.rules.get("preferred_style_examples", []),
        }

    def build_prompt_rules(self, plan: dict) -> list[str]:
        rules = []

        rules.append(f"本段譯文目標：{plan.get('style_target', '台灣繁體中文出版級小說譯文')}。")

        for p in plan.get("principles", []):
            rules.append(p)

        for item in plan.get("matched_rules", []):
            instruction = item.get("instruction", "")
            if instruction:
                rules.append(instruction)

        for forbidden in plan.get("forbidden_style", []):
            rules.append(f"禁止：{forbidden}")

        return rules

    def build_examples(self, plan: dict, max_examples: int = 3) -> list[dict]:
        examples = plan.get("preferred_style_examples", [])
        return examples[:max_examples]

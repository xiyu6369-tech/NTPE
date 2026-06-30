from __future__ import annotations

import json
from pathlib import Path


class LiteraryStyleRulesEngine:
    """
    TQF-06.4.1

    根據韓文原文分析：

    - 心理描寫
    - 動作描寫
    - 場景描寫
    - 比喻
    - 對話節奏

    產生 Prompt Rules。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = (
            self.root
            / "rules"
            / "literary_style_rules.json"
        )

        self.rules = self._load_rules()

    def _load_rules(self):

        if not self.rules_path.exists():
            return {}

        return json.loads(
            self.rules_path.read_text(
                encoding="utf-8-sig"
            )
        )

    def analyze(self, text: str):

        matched = []

        for rule in self.rules.get("rules", []):

            for trigger in rule["triggers"]:

                if trigger in text:

                    matched.append(rule)

                    break

        return {
            "matched_rules": matched,
            "principles":
                self.rules.get(
                    "principles",
                    []
                ),
            "rewrite_preferences":
                self.rules.get(
                    "rewrite_preferences",
                    []
                ),
            "forbidden":
                self.rules.get(
                    "forbidden",
                    []
                )
        }

    def build_prompt_rules(
        self,
        analysis: dict
    ):

        prompt_rules = []

        for item in analysis.get(
            "matched_rules",
            []
        ):

            prompt_rules.append(
                item["instruction"]
            )

        return prompt_rules
from __future__ import annotations

import json
import re
from pathlib import Path

from .semantic_qa import SemanticQA


class SemanticRepair:
    """
    TQF-04 Semantic Auto Repair

    原則：
    - 只做保守修復。
    - 不大幅改寫句子。
    - 可自動處理明確詞彙錯誤與引號格式。
    - 無法安全修復的問題只記錄，不硬改。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.qa = SemanticQA(root)
        self.rules_path = self.root / "rules" / "semantic_repair_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict]:
        if not self.rules_path.exists():
            return []
        data = json.loads(self.rules_path.read_text(encoding="utf-8-sig"))
        return data.get("rules", [])

    def repair(self, source_text: str, translation_text: str) -> dict:
        before = translation_text
        text = translation_text
        applied = []

        text, quote_applied = self._normalize_quotes(text)
        applied.extend(quote_applied)

        for rule in self.rules:
            trigger = rule.get("source_trigger", "")
            if trigger and trigger not in source_text:
                continue

            for item in rule.get("repair", []):
                src_condition = item.get("when_source_contains", "")
                old = item.get("from", "")
                new = item.get("to", "")

                if src_condition and src_condition not in source_text:
                    continue
                if not old or not new:
                    continue

                if old in text:
                    text = text.replace(old, new)
                    applied.append({
                        "rule_id": rule.get("id", ""),
                        "from": old,
                        "to": new,
                        "type": "literal_replace",
                    })

        # 特例：軍靴。避免只把所有「鞋子」無腦換掉。
        if "군화" in source_text and "軍靴" not in text:
            text, did = self._repair_military_boot(text)
            if did:
                applied.append({
                    "rule_id": "SEM_GUNHWA_BOOT",
                    "type": "contextual_replace",
                    "message": "軍靴語義修復",
                })

        # 特例：豆子從筷子掉落，不是筷子掉。
        if "젓가락에서 콩자반이 떨어져" in source_text:
            text, did = self._repair_beans_chopsticks(text)
            if did:
                applied.append({
                    "rule_id": "SEM_BEANS_CHOPSTICKS",
                    "type": "contextual_replace",
                    "message": "豆子/筷子動作修復",
                })

        after_qa = self.qa.check(source_text, text)

        return {
            "changed": before != text,
            "translation": text,
            "applied": applied,
            "qa": after_qa,
        }

    def _normalize_quotes(self, text: str) -> tuple[str, list[dict]]:
        applied = []
        if '"' not in text:
            return text, applied

        chars = []
        open_quote = True

        for ch in text:
            if ch == '"':
                chars.append("「" if open_quote else "」")
                open_quote = not open_quote
            else:
                chars.append(ch)

        new_text = "".join(chars)
        if new_text != text:
            applied.append({
                "rule_id": "STYLE_QUOTES",
                "type": "quote_normalize",
                "from": '"',
                "to": "「」",
            })
        return new_text, applied

    def _repair_military_boot(self, text: str) -> tuple[str, bool]:
        # 優先修「那雙鞋子」「鞋子」等局部表述，避免過度替換。
        patterns = [
            (r"那雙鞋子", "那雙軍靴"),
            (r"那雙靴子", "那雙軍靴"),
            (r"鞋子", "軍靴"),
        ]

        new_text = text
        for old, new in patterns:
            new_text = re.sub(old, new, new_text, count=1)

        return new_text, new_text != text

    def _repair_beans_chopsticks(self, text: str) -> tuple[str, bool]:
        replacements = [
            ("手裡握著的筷子掉落了，豆子也滾到了地上", "手中筷子夾著的醬煮黑豆掉了下來，滾到一旁"),
            ("手中的筷子也掉到了地上", "筷子上夾著的黑豆掉了下來"),
            ("筷子掉落", "筷子上的黑豆掉落"),
            ("筷子也掉", "筷子上的黑豆也掉"),
        ]

        new_text = text
        for old, new in replacements:
            if old in new_text:
                new_text = new_text.replace(old, new)

        return new_text, new_text != text

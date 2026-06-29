from __future__ import annotations

import json
import re
from pathlib import Path


class SemanticQA:
    """
    TQF-04 Semantic QA

    用途：
    - 翻譯後檢查高風險語義錯誤。
    - 不呼叫 AI。
    - 回傳 issues，供 Auto Repair 或後續 QA Retry 使用。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = self.root / "rules" / "semantic_repair_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict]:
        if not self.rules_path.exists():
            return []

        data = json.loads(self.rules_path.read_text(encoding="utf-8-sig"))
        return data.get("rules", [])

    def check(self, source_text: str, translation_text: str) -> dict:
        issues = []

        for rule in self.rules:
            trigger = rule.get("source_trigger", "")
            if trigger and trigger not in source_text:
                continue

            required_any = rule.get("required_any", [])
            forbidden = rule.get("forbidden", [])
            severity = rule.get("severity", "warning")

            if required_any:
                if not any(term in translation_text for term in required_any):
                    issues.append({
                        "id": rule.get("id", ""),
                        "type": "semantic_required_missing",
                        "severity": severity,
                        "message": f"{trigger} 出現時，譯文應包含：{required_any}",
                        "note": rule.get("note", ""),
                    })

            for bad in forbidden:
                if bad and bad in translation_text:
                    issues.append({
                        "id": rule.get("id", ""),
                        "type": "semantic_forbidden_translation",
                        "severity": severity,
                        "message": f"{trigger} 出現時，譯文不應出現「{bad}」。",
                        "note": rule.get("note", ""),
                    })

        quote_issue = self._check_quotes(translation_text)
        if quote_issue:
            issues.append(quote_issue)

        return {
            "passed": not any(i["severity"] == "error" for i in issues),
            "issues": issues,
            "issue_count": len(issues),
        }

    def _check_quotes(self, text: str) -> dict | None:
        # 有英文雙引號且看起來是對話時提示
        if '"' in text:
            return {
                "id": "STYLE_QUOTES",
                "type": "style_quote_format",
                "severity": "info",
                "message": "譯文出現英文雙引號，建議統一為中文引號「」。",
                "note": "Normalize dialogue quotes.",
            }
        return None

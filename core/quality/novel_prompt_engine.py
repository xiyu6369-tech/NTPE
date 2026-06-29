from __future__ import annotations

import json
from pathlib import Path


class NovelPromptEngine:
    """
    TQF-06.1 Novel Prompt Engine

    用途：
    - 將小說翻譯規則結構化。
    - 產生更強的出版級小說翻譯 prompt sections。
    - 不直接翻譯、不呼叫 API。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = self.root / "rules" / "novel_prompt_engine_rules.json"
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        if not self.rules_path.exists():
            return {}
        return json.loads(self.rules_path.read_text(encoding="utf-8-sig"))

    def build_system_prompt(self, target: str) -> str:
        identity = self.rules.get("system_identity", [])
        lines = [
            "你是 NTPE 的專業韓文小說翻譯引擎。",
            f"你的任務是將原文完整翻譯成{target}。",
        ]
        lines.extend(identity)
        lines.append("只輸出譯文，不要加解釋。")
        return "".join(lines)

    def build_sections(self, chunk_text: str) -> dict:
        return {
            "target": self.rules.get("target", "台灣繁體中文出版級韓文小說譯文"),
            "literary_rules": self.rules.get("literary_rules", []),
            "taiwan_style_rules": self.rules.get("taiwan_style_rules", []),
            "dialogue_rules": self.rules.get("dialogue_rules", []),
            "forbidden_rules": self.rules.get("forbidden_rules", []),
            "focus": self._detect_focus(chunk_text),
        }

    def build_prompt_rules(self, sections: dict) -> list[str]:
        rules = []
        rules.append(f"譯文目標：{sections.get('target')}。")

        for group in ["literary_rules", "taiwan_style_rules", "dialogue_rules", "forbidden_rules"]:
            for item in sections.get(group, []):
                rules.append(item)

        for item in sections.get("focus", []):
            rules.append(item)

        return rules

    def _detect_focus(self, text: str) -> list[str]:
        focus = []
        text = text or ""

        if any(k in text for k in ["예감", "기분", "생각", "불길", "우울", "난감"]):
            focus.append("本段含心理或情緒描寫，必須保留內心轉折與語氣層次。")

        if any(k in text for k in ["말했다", "물었다", "중얼거렸다", "웃었다", "노려보았다"]):
            focus.append("本段含對話或人物反應，需保持對話自然與人物口吻差異。")

        if any(k in text for k in ["비", "소리", "군화", "초인종", "계단", "현관"]):
            focus.append("本段含聲音、空間或場景描寫，需保留畫面感與氛圍。")

        if any(k in text for k in ["역병신", "다를 바 없는", "처럼"]):
            focus.append("本段含比喻或意象，必須保留其文學效果。")

        if any(k in text for k in ["……", "...", "—", "--"]):
            focus.append("本段含停頓或省略號，需保留沉默、猶豫或語氣停頓。")

        return focus

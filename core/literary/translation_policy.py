from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteraryTranslationPolicy:
    """Compact v3 literary translation policy.

    The policy is intentionally short.  The old PS-04 prompt carried too many
    repeated rules into every request; v3 keeps the fixed policy compact and
    leaves token budget for the actual novel text.
    """

    name: str = "literary-traditional-chinese-v3"
    version: str = "1.2-ter-v1.2-literary-style-engine"

    def system_identity(self) -> str:
        return (
            "你是專業韓文小說譯者。先理解劇情、主詞、人物關係、語氣與場景，"
            "再翻成自然流暢、符合故事背景的繁體中文小說。只輸出譯文。"
        )

    def rules(self) -> list[str]:
        return [
            "忠於原文：不漏譯、不摘要、不新增劇情或設定。",
            "先判斷主詞與行為者，避免把甲的動作或心理翻成乙。",
            "Glossary 中的人名、地名、術語必須逐字一致；不可改音譯。",
            "用語依作品時代、地點、人物與氛圍決定，不刻意套用特定地區中文。",
            "心理描寫與慣用語依上下文轉成自然中文；不要機械直譯。",
            "中文要像小說敘事，不要像摘要、說明文或逐字翻譯。",
            "動作描寫採中文小說慣用表達，例如挑眉、轉身離去、倚牆坐下；不得添加原文沒有的動作。",
            "對話使用「」；不得輸出註解、標題、Markdown 或分析。",
        ]

    def render(self) -> str:
        return "【Policy】\n" + "\n".join(f"- {rule}" for rule in self.rules())

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
    version: str = "1.2-ter-v1.3-speed-prompt-compression"

    def system_identity(self) -> str:
        return "專業韓文小說譯者。理解主詞、人物、語氣與場景後，直出自然繁體中文小說正文。"

    def rules(self) -> list[str]:
        return [
            "忠於原文，不漏譯、不摘要、不新增劇情。",
            "先判斷主詞與行為者，避免人物錯置。",
            "Glossary 譯名必須逐字一致。",
            "用語依作品背景自然選擇，不刻意地區化。",
            "慣用語與心理描寫用自然中文，不機械直譯。",
            "只輸出譯文；對話用「」。",
        ]

    def render(self) -> str:
        return "【Policy】\n" + "；".join(self.rules())

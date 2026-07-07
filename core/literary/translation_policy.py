from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteraryTranslationPolicy:
    """Compact v3 literary translation policy.

    The policy is intentionally short.  The old PS-04 prompt carried too many
    repeated rules into every request; v3 keeps the fixed policy compact and
    leaves token budget for the actual novel text.
    """

    name: str = "literary-traditional-chinese-v5"
    version: str = "1.2-ter-v1.5-literary-polish-v2"

    def system_identity(self) -> str:
        return "韓文小說譯者。先判斷主詞與語氣，再直出自然繁體中文正文。"

    def rules(self) -> list[str]:
        return [
            "忠於原文，不漏譯、不增刪。",
            "先判斷主詞、行為者與指代，避免人物錯置。",
            "Glossary 譯名逐字一致。",
            "慣用語按中文小說語感處理，不機械直譯。",
            "短答、反諷、模稜兩可語氣需保留，不擅自解釋。",
            "避免生硬直譯，動作與心理描寫需像中文小說正文。",
            "只輸出繁體中文譯文，對話用「」。",
        ]

    def render(self) -> str:
        return "【Policy】" + "；".join(self.rules())

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def glossary_text(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "（無）"
    items = []
    for src, dst in sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True):
        items.append(f"- {src} => {dst}")
    return "\n".join(items)


@dataclass
class PromptEngine:
    """Builds translation prompts only. No validation, no polishing, no self-review."""

    novel_profile: str = "韓文長篇小說，現代背景，重視心理描寫、人物語氣與敘事節奏。"

    def build_translate_prompt(self, text: str, context: str = "", glossary: Dict[str, str] | None = None) -> str:
        glossary = glossary or {}
        context_block = context.strip() if context and context.strip() else "（無）"
        glossary_block = glossary_text(glossary)

        return f"""
你是專業韓文小說譯者。請執行「忠實小說翻譯」，不是摘要、改寫、解釋、潤稿或創作。

【作品類型】
{self.novel_profile}

【絕對規則】
1. 只能翻譯原文中存在的資訊，不得新增任何原文沒有寫出的心理、原因、結論或背景。
2. 不得摘要，不得壓縮，不得合併事件，不得省略心理描寫、修飾語、動作、對話與括號內容。
3. 原文是暗示，譯文也必須保留暗示；原文沒有直接下判斷，譯文不能替作者下判斷。
4. 不得把敘述改成解釋，不得把角色反應改成評論。
5. 使用自然流暢的繁體中文小說文體，不刻意台灣化，也不刻意中國化。
6. 對話使用「」。
7. 固定譯名必須完全遵守。
8. 只輸出譯文，不要輸出任何說明、標題、註解或前後綴。

【禁止示例】
- 不得把「男人看著他」翻成「男人討厭他」。
- 不得把「神情冷淡」翻成「他是種族主義者」。
- 不得把「他皺眉」翻成「他覺得很不舒服」。
- 不得自行補上「因此、所以、他知道、他認為」等原文沒有明確表達的推論。

【固定譯名】
{glossary_block}

【前文參考】
{context_block}

【待翻譯內容】
{text}
""".strip()

    # Compatibility with older code that may call build(...)
    def build(self, text: str, context: str = "", glossary: Dict[str, str] | None = None) -> str:
        return self.build_translate_prompt(text=text, context=context, glossary=glossary)

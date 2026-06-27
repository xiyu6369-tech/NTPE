from dataclasses import dataclass
from typing import Dict


def glossary_text(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "（無）"
    lines = []
    for src, dst in sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True):
        lines.append(f"- {src} = {dst}")
    return "\n".join(lines)


@dataclass
class TranslationPolicy:
    """NTPE Translation Policy 1.0

    核心原則：AI 只能翻譯，不得創作。
    這份政策同時用於翻譯 Prompt 與 Self Check。
    """

    name: str = "NTPE Translation Policy 1.0"

    def rules_text(self) -> str:
        return """
【翻譯政策：絕對遵守】
1. 你只能翻譯原文實際存在的資訊，不得新增、補完、推論、解釋。
2. 不得替角色補心理活動；原文沒有明說，就不能寫成確定想法或感受。
3. 不得把作者的暗示、留白、語氣寫成明確結論。
4. 不得把描述改寫成總結；不得把多個細節合併成一句大意。
5. 不得刪減心理描寫、修飾語、動作、對話、括號內容。
6. 不得自行美化、擴寫、重組劇情順序。
7. 不得加入「他知道」「他認為」「他覺得」「他感到」等原文沒有的心理判斷。
8. 對話使用「」。
9. 使用自然流暢的繁體中文小說文體，不刻意台灣化，也不刻意中國化。
10. 只輸出譯文，不要輸出說明、標題、註解。
""".strip()

    def self_check_text(self) -> str:
        return """
【自我檢查標準】
請只判斷譯文是否違反以下任一項：
1. 新增原文沒有的資訊。
2. 刪除原文存在的重要資訊。
3. 將暗示或留白改成確定結論。
4. 替角色補出原文沒有的心理活動。
5. 將細節摘要成大意。
6. 人名或術語不符合固定譯名。
7. 譯文殘留大量韓文。

輸出格式只能是：
PASS
或
FAIL: 原因
""".strip()


class PromptEngine:
    def __init__(self, profile_name: str = "PASSION"):
        self.profile_name = profile_name
        self.policy = TranslationPolicy()

    def build_translation_prompt(self, text: str, context: str, glossary: Dict[str, str]) -> str:
        profile = self._profile_text()
        return f"""
你是專業韓文小說譯者。你的任務是忠實翻譯，不是摘要、改寫、潤稿或創作。

【小說設定】
{profile}

{self.policy.rules_text()}

【固定譯名】
{glossary_text(glossary)}

【前文參考】
{context if context else "（無）"}

【待翻譯內容】
{text}
""".strip()

    def build_self_check_prompt(self, source: str, translated: str, glossary: Dict[str, str]) -> str:
        return f"""
你是翻譯品質檢查員。請比對韓文原文與繁體中文譯文。
你的工作不是潤稿，不要重寫譯文，只判斷是否符合規則。

{self.policy.self_check_text()}

【固定譯名】
{glossary_text(glossary)}

【韓文原文】
{source}

【中文譯文】
{translated}
""".strip()

    def _profile_text(self) -> str:
        if self.profile_name.upper() == "PASSION":
            return """
作品類型：現代韓文長篇小說。
文體要求：成熟、冷靜、保留心理描寫與作者留白。
翻譯目標：忠於原文，再保持中文自然。
特別要求：不要替角色下判斷，不要把曖昧寫成確定事實。
""".strip()
        return """
作品類型：韓文長篇小說。
文體要求：保留原作語氣、節奏、心理描寫與作者留白。
翻譯目標：忠於原文，再保持中文自然。
""".strip()

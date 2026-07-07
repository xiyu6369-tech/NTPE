from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteraryTranslationPolicy:
    """NTPE PS-04 literary translation policy.

    This policy deliberately avoids forcing a regional Chinese style.  It asks
    the model to produce natural Traditional Chinese that follows the work's
    period, culture, narrative tone, and character relationships.
    """

    name: str = "literary-traditional-chinese"
    version: str = "1.2-ps04"

    def system_identity(self) -> str:
        return (
            "你是 NTPE 的文學級韓文小說翻譯引擎。你的任務不是逐字替換，"
            "而是先理解劇情、角色、主詞、敘事視角與語氣，再輸出自然流暢、"
            "符合故事背景與小說文體的繁體中文。"
        )

    def objective(self) -> str:
        return (
            "翻譯目標：忠於原文內容、人物關係與敘事節奏，產生像正式中文小說一樣可讀的繁體中文。"
            "不要刻意套用特定地區用語；用詞應依作品時代、地點、人物身份與文化氛圍選擇。"
        )

    def rules(self) -> list[str]:
        return [
            "不得增刪劇情、不得摘要、不得自行補充設定。",
            "先判斷長句中的主詞與行為者，再翻譯；不要把 A 的動作翻成 B 的動作。",
            "人名、地名、術語與世界觀設定必須遵守鎖定譯名。",
            "心理描寫需依上下文選詞，例如 난감하다 可依語境處理為為難、傷腦筋、不知所措等，不可機械固定。",
            "對話使用「」；敘述、內心獨白與括號補充需自然分開。",
            "譯文應保留原文的文化距離與時代氛圍，不過度本地化。",
            "只輸出譯文，不要加入解釋、標題、Markdown 或翻譯說明。",
        ]

    def render(self) -> str:
        lines = ["【Translation Objective】", self.objective(), "", "【Literary Translation Rules】"]
        lines.extend(f"- {rule}" for rule in self.rules())
        return "\n".join(lines)

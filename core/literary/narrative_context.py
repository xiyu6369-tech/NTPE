from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NarrativeContext:
    perspective: str = "第三人稱小說敘事"
    hints: list[str] = field(default_factory=list)

    @classmethod
    def analyze(cls, chunk_text: str, previous_context: str = "") -> "NarrativeContext":
        hints: list[str] = []
        if any(token in chunk_text for token in ("호텔", "로비", "섬", "바닷가", "라군")):
            hints.append("場景含酒店／大廳／島嶼／海邊等度假場域；用詞依作品背景自然選擇。")
        if "베를린" in chunk_text or "독일" in chunk_text:
            hints.append("含德國／柏林背景；保留作品文化距離，不刻意本地化。")
        if "난감" in chunk_text:
            hints.append("난감하다 依語境處理為為難、傷腦筋、不知如何是好等心理狀態。")
        if "카일이" in chunk_text and "주장" in chunk_text:
            hints.append("카일이 주장... 結構中，主張與相關動作優先歸於凱爾。")
        if any(len(p) > 220 for p in chunk_text.splitlines()):
            hints.append("本段有長句；先切分敘事單位，再保持主詞與行為者正確。")
        return cls(hints=hints[:6])

    def render(self) -> str:
        if not self.hints:
            return "【Narrative】依原文判斷敘事、場景與情緒"
        return "【Narrative】" + "；".join(self.hints)

    def to_dict(self) -> dict:
        return {"perspective": self.perspective, "hints": self.hints}

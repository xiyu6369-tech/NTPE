from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


KNOWN_CHARACTER_HINTS = {
    "정태의": {"zh": "鄭泰義", "voice": "自然、反應快、帶自我吐槽感"},
    "카일": {"zh": "凱爾", "voice": "理性，但情緒被觸及時強硬"},
    "일라이": {"zh": "伊萊", "voice": "冷、短、直接、有壓迫感"},
    "일레이": {"zh": "伊萊", "voice": "冷、短、直接、有壓迫感"},
}


@dataclass
class CharacterContext:
    current_focus: list[str] = field(default_factory=list)
    mentioned: dict[str, dict[str, str]] = field(default_factory=dict)
    subject_hints: list[str] = field(default_factory=list)

    @classmethod
    def analyze(cls, chunk_text: str, locked_dictionary: Mapping[str, str], previous_context: str = "") -> "CharacterContext":
        mentioned: dict[str, dict[str, str]] = {}
        focus: list[str] = []
        subject_hints: list[str] = []
        for src, target in locked_dictionary.items():
            if src and src in chunk_text:
                info = dict(KNOWN_CHARACTER_HINTS.get(src, {}))
                info.setdefault("zh", target)
                info.setdefault("voice", "依上下文")
                mentioned[src] = info
                focus.append(target)
        if "정태의는 난감" in chunk_text:
            subject_hints.append("鄭泰義是心理描寫主體；난감 不等於身體不舒服。")
        if "카일이" in chunk_text and "주장" in chunk_text:
            subject_hints.append("凱爾是『主張／堅持說』的主體，後續相關行為不要誤歸鄭泰義。")
        return cls(current_focus=focus[:4], mentioned=mentioned, subject_hints=subject_hints[:4])

    def render(self) -> str:
        parts: list[str] = []
        if self.mentioned:
            rows = [f"{src}={info.get('zh', '')}" for src, info in self.mentioned.items()]
            parts.append("【Characters】" + "；".join(rows))
        if self.subject_hints:
            parts.append("【Subject】" + "；".join(self.subject_hints))
        return "\n".join(parts) if parts else "【Characters】依原文判斷"

    def to_dict(self) -> dict:
        return {"current_focus": self.current_focus, "mentioned": self.mentioned, "subject_hints": self.subject_hints}

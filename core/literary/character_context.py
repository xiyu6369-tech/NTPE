from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


KNOWN_CHARACTER_HINTS = {
    "정태의": {"zh": "鄭泰義", "role": "主要敘事焦點之一", "voice": "自然、反應快、帶有自我吐槽感"},
    "카일": {"zh": "凱爾", "role": "與鄭泰義同行的人物", "voice": "理性但偶爾強硬"},
    "일라이": {"zh": "伊萊", "role": "壓迫感強的人物", "voice": "冷、短、直接"},
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
                info.setdefault("role", "本段出現人物")
                mentioned[src] = info
                if src not in focus:
                    focus.append(src)

        # Korean subject markers; useful for prompt guidance, not hard parsing.
        for src in mentioned:
            if f"{src}는" in chunk_text or f"{src}은" in chunk_text:
                subject_hints.append(f"{mentioned[src]['zh']} 可能是敘事焦點或心理描寫主體。")
            if f"{src}가" in chunk_text or f"{src}이" in chunk_text:
                subject_hints.append(f"{mentioned[src]['zh']} 可能是本句明確行為主體。")

        if "카일이" in chunk_text and "주장" in chunk_text:
            subject_hints.append("含有 카일이 주장... 結構時，主張與後續相關動作應優先歸於凱爾，不要誤歸於鄭泰義。")
        if "정태의는 난감" in chunk_text:
            subject_hints.append("정태의는 난감... 表示鄭泰義感到為難或傷腦筋，不宜機械翻成身體不舒服。")

        return cls(current_focus=focus[:3], mentioned=mentioned, subject_hints=subject_hints)

    def render(self) -> str:
        if not self.mentioned:
            characters = "- 無明確鎖定人物"
        else:
            rows = []
            for src, info in self.mentioned.items():
                rows.append(
                    f"- {src} → {info.get('zh', '')}；角色：{info.get('role', '本段出現人物')}；語氣參考：{info.get('voice', '依上下文')}"
                )
            characters = "\n".join(rows)
        focus = "、".join(self.current_focus) if self.current_focus else "依原文判斷"
        hints = "\n".join(f"- {hint}" for hint in self.subject_hints) or "- 無"
        return f"【Character Context】\n目前可能敘事焦點：{focus}\n{characters}\n\n【Subject / Pronoun Hints】\n{hints}"

    def to_dict(self) -> dict:
        return {
            "current_focus": self.current_focus,
            "mentioned": self.mentioned,
            "subject_hints": self.subject_hints,
        }

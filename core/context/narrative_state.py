from __future__ import annotations

from .context_serializer import now_iso


class NarrativeState:
    def __init__(self, data: dict | None = None):
        self.data = data or {
            "person": "第三人稱",
            "tone": "",
            "emotion_flow": [],
            "narrative_focus": [],
            "updated_at": now_iso(),
        }

    def update(self, *, source_text: str, translation_text: str = "") -> dict:
        tone = ""
        if "불길" in source_text:
            tone = "不祥、壓抑"
        elif "우울" in source_text:
            tone = "鬱悶"
        elif "난감" in source_text:
            tone = "困擾"
        elif "신경질" in source_text:
            tone = "煩躁"

        if tone:
            self.data["tone"] = tone
            flow = self.data.setdefault("emotion_flow", [])
            flow.append(tone)
            self.data["emotion_flow"] = flow[-8:]

        focus = set(self.data.get("narrative_focus", []))

        if any(k in source_text for k in ["예감", "기분", "생각"]):
            focus.add("心理描寫")
        if any(k in source_text for k in ["비", "소리", "군화", "초인종"]):
            focus.add("場景與聲音")
        if any(k in source_text for k in ["말했다", "물었다", "중얼거렸다"]):
            focus.add("對話")
        if any(k in source_text for k in ["역병신", "처럼", "다를 바 없는"]):
            focus.add("比喻意象")

        self.data["narrative_focus"] = sorted(focus)[-8:]
        self.data["updated_at"] = now_iso()
        return self.data

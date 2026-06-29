from __future__ import annotations

from .context_serializer import now_iso


class CharacterState:
    NAME_MAP = {
        "정태의": "鄭泰義",
        "정재의": "鄭載義",
        "일라이": "伊萊",
        "리그로우": "里格勞",
        "카일": "凱爾",
        "삼촌": "叔叔",
        "형": "哥哥",
    }

    def __init__(self, data: dict | None = None):
        self.data = data or {
            "characters": {},
            "active_characters": [],
            "updated_at": now_iso(),
        }

    def update(self, *, source_text: str, translation_text: str = "") -> dict:
        active = list(self.data.get("active_characters", []))
        characters = self.data.setdefault("characters", {})

        for ko, zh in self.NAME_MAP.items():
            if ko in source_text or zh in translation_text:
                if zh not in active:
                    active.append(zh)
                state = characters.setdefault(zh, {
                    "aliases": [],
                    "emotion": "",
                    "focus": "",
                    "notes": [],
                    "last_seen": "",
                })
                if ko not in state["aliases"]:
                    state["aliases"].append(ko)
                state["last_seen"] = now_iso()

        taeui = characters.get("鄭泰義")
        if taeui:
            if "불길" in source_text or "예감" in source_text:
                taeui["emotion"] = "不祥預感、警戒"
            if "신경질" in source_text:
                taeui["emotion"] = "煩躁"
            if "현관" in source_text:
                taeui["focus"] = "玄關"
            if "무릎" in source_text and "膝蓋疼痛" not in taeui["notes"]:
                taeui["notes"].append("膝蓋疼痛")

        self.data["active_characters"] = active[-8:]
        self.data["updated_at"] = now_iso()
        return self.data

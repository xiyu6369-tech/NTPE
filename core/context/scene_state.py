from __future__ import annotations

from .context_serializer import now_iso


class SceneState:
    def __init__(self, data: dict | None = None):
        self.data = data or {
            "location": "",
            "time": "",
            "weather": "",
            "mood": "",
            "objects": [],
            "updated_at": now_iso(),
        }

    def update(self, *, source_text: str, translation_text: str = "") -> dict:
        if "현관" in source_text:
            self.data["location"] = "玄關"
        elif "계단" in source_text:
            self.data["location"] = "樓梯"
        elif "소파" in source_text:
            self.data["location"] = "沙發"
        elif "연립주택" in source_text:
            self.data["location"] = "老舊連棟住宅"

        if "비" in source_text:
            self.data["weather"] = "雨天"
        if "아침" in source_text or "7시" in source_text:
            self.data["time"] = "清晨"
        if "불길" in source_text or "예감" in source_text:
            self.data["mood"] = "不祥預感"

        objects = set(self.data.get("objects", []))
        mapping = {
            "초인종": "門鈴",
            "군화": "軍靴",
            "제복": "制服",
            "정복": "正裝制服",
            "콩자반": "醬煮黑豆",
            "젓가락": "筷子",
        }
        for ko, zh in mapping.items():
            if ko in source_text:
                objects.add(zh)

        self.data["objects"] = sorted(objects)[-12:]
        self.data["updated_at"] = now_iso()
        return self.data

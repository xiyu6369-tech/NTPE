from __future__ import annotations

from .context_serializer import now_iso


class StoryState:
    def __init__(self, data: dict | None = None):
        self.data = data or {
            "current_file": "",
            "current_chunk": 0,
            "recent_events": [],
            "updated_at": now_iso(),
        }

    def update(self, *, file_name: str, chunk_index: int, source_text: str, translation_text: str = "") -> dict:
        self.data["current_file"] = file_name
        self.data["current_chunk"] = chunk_index
        self.data["updated_at"] = now_iso()

        event = self._detect_event(source_text, translation_text)
        if event:
            events = self.data.setdefault("recent_events", [])
            events.append({
                "file": file_name,
                "chunk": chunk_index,
                "event": event,
                "updated_at": now_iso(),
            })
            self.data["recent_events"] = events[-8:]

        return self.data

    def _detect_event(self, source_text: str, translation_text: str = "") -> str:
        if "초인종" in source_text:
            return "門鈴響起，打斷目前場景。"
        if "군화" in source_text:
            return "出現軍靴或具軍事氣息的人物。"
        if "공항" in source_text:
            return "人物剛從機場抵達。"
        if "비" in source_text:
            return "場景與雨天或陰鬱天氣有關。"
        return translation_text.strip()[:120] if translation_text else ""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class VoiceMemory:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / "memory" / "character_voice_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.path.exists():
            return {"characters": {}, "updated_at": now_iso()}
        try:
            return json.loads(self.path.read_text(encoding="utf-8-sig"))
        except Exception:
            return {"characters": {}, "updated_at": now_iso()}

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def update_seen(self, matches: list[dict], *, file_name: str = "", chunk_index: int = 0) -> dict:
        data = self.load()
        chars = data.setdefault("characters", {})
        for item in matches:
            name = item["target_name"]
            state = chars.setdefault(name, {
                "seen_count": 0,
                "last_seen_file": "",
                "last_seen_chunk": 0,
                "voice": item.get("voice", []),
            })
            state["seen_count"] += 1
            state["last_seen_file"] = file_name
            state["last_seen_chunk"] = chunk_index
            state["voice"] = item.get("voice", [])
        self.save(data)
        return data

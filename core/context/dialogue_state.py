from __future__ import annotations

import re
from .context_serializer import now_iso


class DialogueState:
    def __init__(self, data: dict | None = None):
        self.data = data or {
            "in_dialogue": False,
            "recent_dialogue": [],
            "last_speaker": "",
            "updated_at": now_iso(),
        }

    def update(self, *, source_text: str, translation_text: str = "") -> dict:
        lines = []

        for match in re.findall(r"「([^」]+)」", translation_text or ""):
            lines.append({"speaker": "", "text": match.strip(), "source": "translation"})

        if not lines:
            for match in re.findall(r'"([^"]+)"', source_text or ""):
                lines.append({"speaker": "", "text": match.strip(), "source": "source"})

        if lines:
            self.data["in_dialogue"] = True
            recent = self.data.setdefault("recent_dialogue", [])
            recent.extend(lines)
            self.data["recent_dialogue"] = recent[-6:]
        else:
            self.data["in_dialogue"] = False

        self.data["updated_at"] = now_iso()
        return self.data

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
VOICE = ROOT / "core" / "voice"
RULES = ROOT / "rules"

VOICE.mkdir(parents=True, exist_ok=True)
RULES.mkdir(parents=True, exist_ok=True)

(RULES / "character_voice_rules.json").write_text(json.dumps({
    "version": "1.0",
    "module": "TQF-06.3 Character Voice Engine",
    "profiles": {
        "鄭泰義": {
            "source_names": ["정태의"],
            "voice": ["自然", "帶吐槽感", "內心戲多", "反應快"],
            "dialogue_style": "自然口語，但不要幼稚；可保留吐槽與無奈感。",
            "narration_style": "心理描寫要細膩，保留警戒、煩躁、不祥預感。",
            "avoid": ["過度禮貌", "過度文雅", "像旁白一樣說話"]
        },
        "叔叔": {
            "source_names": ["삼촌"],
            "voice": ["成熟", "沉穩", "直接", "軍人氣息"],
            "dialogue_style": "語氣穩定、簡潔，不使用年輕化口吻。",
            "narration_style": "出場時保留壓迫感與正式感。",
            "avoid": ["輕浮", "過度親暱", "年輕人口氣"]
        },
        "伊萊": {
            "source_names": ["일라이"],
            "voice": ["冷靜", "危險", "壓迫感", "簡短"],
            "dialogue_style": "句子偏短，語氣平靜但有壓迫感。",
            "narration_style": "保留危險、不可預測、壓迫性的氛圍。",
            "avoid": ["熱情", "誇張", "解釋太多"]
        },
        "鄭載義": {
            "source_names": ["정재의"],
            "voice": ["神祕", "玩世不恭", "輕描淡寫"],
            "dialogue_style": "可帶一點曖昧與玩笑感，但不可油膩。",
            "narration_style": "保留難以捉摸與幸運感。",
            "avoid": ["過度正經", "說教"]
        }
    }
}, ensure_ascii=False, indent=2), encoding="utf-8")

(VOICE / "__init__.py").write_text('''from .voice_profile import VoiceProfile
from .voice_memory import VoiceMemory

__all__ = [
    "VoiceProfile",
    "VoiceMemory",
]
''', encoding="utf-8")

(VOICE / "voice_profile.py").write_text('''from __future__ import annotations

import json
from pathlib import Path


class VoiceProfile:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / "rules" / "character_voice_rules.json"
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"profiles": {}}
        return json.loads(self.path.read_text(encoding="utf-8-sig"))

    def profiles(self) -> dict:
        return self.data.get("profiles", {})

    def match(self, text: str) -> list[dict]:
        results = []
        for target_name, profile in self.profiles().items():
            source_names = profile.get("source_names", [])
            if target_name in text or any(name in text for name in source_names):
                results.append({
                    "target_name": target_name,
                    "source_names": source_names,
                    "voice": profile.get("voice", []),
                    "dialogue_style": profile.get("dialogue_style", ""),
                    "narration_style": profile.get("narration_style", ""),
                    "avoid": profile.get("avoid", []),
                })
        return results

    def build_prompt_rules(self, matches: list[dict]) -> list[str]:
        rules = []
        for item in matches:
            name = item["target_name"]
            voice = "、".join(item.get("voice", []))
            if voice:
                rules.append(f"{name} 的人物語氣：{voice}。")
            if item.get("dialogue_style"):
                rules.append(f"{name} 對話風格：{item['dialogue_style']}")
            if item.get("narration_style"):
                rules.append(f"{name} 敘事呈現：{item['narration_style']}")
            if item.get("avoid"):
                rules.append(f"{name} 避免：{'、'.join(item['avoid'])}。")
        return rules
''', encoding="utf-8")

(VOICE / "voice_memory.py").write_text('''from __future__ import annotations

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
''', encoding="utf-8")

print("TQF-06.3 voice batch 1 created.")
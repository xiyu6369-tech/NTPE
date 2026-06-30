from __future__ import annotations

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

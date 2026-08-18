from __future__ import annotations

from pathlib import Path

from core.project_profile import load_project_profile
from .utils import load_json


class PromptBuilderLoader:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def load_profile(self, profile_path: str | Path | None = None) -> dict:
        if profile_path is None:
            profile_path = self.root / "profiles" / "passion_profile.json"
        return load_project_profile(profile_path)

    def load_character_match_dictionary(self, profile: dict) -> dict:
        return load_json(self.root / profile["knowledge_sources"]["character_match_dictionary"])

    def load_glossary(self, profile: dict) -> dict:
        data = load_json(self.root / profile["knowledge_sources"]["glossary"])
        return data.get("terms", data)

    def load_knowledge_base(self, profile: dict) -> dict:
        return load_json(self.root / profile["knowledge_sources"]["knowledge_base"])

    def load_all(self, profile_path: str | Path | None = None) -> dict:
        profile = self.load_profile(profile_path)
        return {
            "profile": profile,
            "character_match_dictionary": self.load_character_match_dictionary(profile),
            "glossary": self.load_glossary(profile),
            "knowledge_base": self.load_knowledge_base(profile),
        }

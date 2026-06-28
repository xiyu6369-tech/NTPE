from __future__ import annotations

from pathlib import Path

from .loader import PromptBuilderLoader
from .character_selector import CharacterSelector
from .glossary_selector import GlossarySelector
from .rule_generator import RuleGenerator
from .prompt_renderer import PromptRenderer
from .package_builder import PackageBuilder
from .utils import save_json


class PromptBuilder:
    def __init__(self, root: str | Path, profile_path: str | Path | None = None):
        self.root = Path(root)
        self.loader = PromptBuilderLoader(self.root)
        self.data = self.loader.load_all(profile_path)

        self.profile = self.data["profile"]
        self.character_selector = CharacterSelector(self.data["character_match_dictionary"])
        self.glossary_selector = GlossarySelector(self.data["glossary"])
        self.rule_generator = RuleGenerator(self.profile)
        self.renderer = PromptRenderer()
        self.package_builder = PackageBuilder()

    def build(self, *, chunk_text: str, file_name: str, chunk_index: int, chunk_total: int, session_id: str, context: dict | None = None) -> dict:
        if context is None:
            context = {
                "previous_summary": "",
                "previous_chunk_tail": "",
                "recent_characters": [],
                "recent_terms": [],
            }

        character_matches = self.character_selector.select(chunk_text)
        glossary_matches = self.glossary_selector.select(chunk_text)
        rules = self.rule_generator.generate()

        prompt = self.renderer.render(
            profile=self.profile,
            chunk_text=chunk_text,
            character_matches=character_matches,
            glossary_matches=glossary_matches,
            rules=rules,
            context=context,
        )

        return self.package_builder.build(
            profile=self.profile,
            chunk_text=chunk_text,
            file_name=file_name,
            chunk_index=chunk_index,
            chunk_total=chunk_total,
            session_id=session_id,
            character_matches=character_matches,
            glossary_matches=glossary_matches,
            rules=rules,
            prompt=prompt,
            context=context,
        )

    def save_package(self, package: dict, path: str | Path) -> None:
        save_json(path, package)

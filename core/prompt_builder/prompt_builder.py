from __future__ import annotations

from pathlib import Path

from .loader import PromptBuilderLoader
from .character_selector import CharacterSelector
from .glossary_selector import GlossarySelector
from .rule_generator import RuleGenerator
from .prompt_renderer import PromptRenderer
from .package_builder import PackageBuilder
from .utils import save_json

try:
    from core.quality.semantic_engine import SemanticTranslationEngine
except Exception:
    SemanticTranslationEngine = None

try:
    from core.quality.structure_engine import DocumentStructureEngine
except Exception:
    DocumentStructureEngine = None

try:
    from core.quality.novel_style_planner import NovelStylePlanner
except Exception:
    NovelStylePlanner = None

try:
    from core.quality.novel_prompt_engine import NovelPromptEngine
except Exception:
    NovelPromptEngine = None


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

        self.semantic_engine = SemanticTranslationEngine(self.root) if SemanticTranslationEngine else None
        self.structure_engine = DocumentStructureEngine(self.root) if DocumentStructureEngine else None
        self.style_planner = NovelStylePlanner(self.root) if NovelStylePlanner else None
        self.novel_prompt_engine = NovelPromptEngine(self.root) if NovelPromptEngine else None

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
        semantic_matches = self.semantic_engine.select(chunk_text) if self.semantic_engine else []
        document_structure = self.structure_engine.analyze(chunk_text) if self.structure_engine else {
            "has_title": False,
            "title": None,
            "elements": [],
        }

        style_plan = self.style_planner.plan(chunk_text) if self.style_planner else {
            "style_target": "台灣繁體中文出版級小說譯文",
            "principles": [],
            "matched_rules": [],
            "forbidden_style": [],
            "preferred_style_examples": [],
        }

        novel_prompt_sections = self.novel_prompt_engine.build_sections(chunk_text) if self.novel_prompt_engine else {}

        rules = self.rule_generator.generate()

        if self.semantic_engine and semantic_matches:
            rules.setdefault("semantic_rules", [])
            rules["semantic_rules"].extend(self.semantic_engine.build_prompt_rules(semantic_matches))

        if self.style_planner and style_plan:
            rules.setdefault("novel_style_rules", [])
            rules["novel_style_rules"].extend(self.style_planner.build_prompt_rules(style_plan))

        if self.novel_prompt_engine and novel_prompt_sections:
            rules.setdefault("novel_prompt_rules", [])
            rules["novel_prompt_rules"].extend(self.novel_prompt_engine.build_prompt_rules(novel_prompt_sections))

        prompt = self.renderer.render(
            profile=self.profile,
            chunk_text=chunk_text,
            character_matches=character_matches,
            glossary_matches=glossary_matches,
            semantic_matches=semantic_matches,
            document_structure=document_structure,
            style_plan=style_plan,
            novel_prompt_sections=novel_prompt_sections,
            rules=rules,
            context=context,
            novel_prompt_engine=self.novel_prompt_engine,
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
            semantic_matches=semantic_matches,
            document_structure=document_structure,
            style_plan=style_plan,
            novel_prompt_sections=novel_prompt_sections,
            rules=rules,
            prompt=prompt,
            context=context,
        )

    def save_package(self, package: dict, path: str | Path) -> None:
        save_json(path, package)

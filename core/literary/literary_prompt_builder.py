from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .character_context import CharacterContext
from .glossary_context import GlossaryContext
from .literary_profile import normalize_profile, profile_guidance
from .narrative_context import NarrativeContext
from .translation_policy import LiteraryTranslationPolicy


@dataclass
class LiteraryPromptResult:
    system_prompt: str
    user_prompt: str
    narrative_context: NarrativeContext
    character_context: CharacterContext
    glossary_context: GlossaryContext
    profile: str

    def to_prompt_dict(self) -> dict:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "prompt_mode": "literary_narrative_understanding_ps04",
            "profile": self.profile,
            "narrative_context": self.narrative_context.to_dict(),
            "character_context": self.character_context.to_dict(),
            "glossary_context": self.glossary_context.to_dict(),
        }


class LiteraryPromptBuilder:
    """Builds PS-04 narrative-aware literary prompts.

    The builder does not rewrite the source.  It gives the model structured
    context before translation: policy, narrative hints, character hints,
    locked glossary, previous context, and current text.
    """

    def __init__(self, policy: LiteraryTranslationPolicy | None = None):
        self.policy = policy or LiteraryTranslationPolicy()

    def build(
        self,
        *,
        chunk_text: str,
        locked_dictionary: Mapping[str, str],
        alias_map: Mapping[str, str] | None = None,
        previous_context: str = "",
        profile: str = "literary",
    ) -> LiteraryPromptResult:
        normalized_profile = normalize_profile(profile)
        glossary = GlossaryContext.from_locked_dictionary(locked_dictionary, chunk_text, alias_map=alias_map)
        character = CharacterContext.analyze(chunk_text, locked_dictionary, previous_context=previous_context)
        narrative = NarrativeContext.analyze(chunk_text, previous_context=previous_context)

        system_prompt = (
            f"{self.policy.system_identity()} "
            "請嚴格遵守鎖定譯名與敘事主詞，並只輸出譯文。"
        )

        user_prompt = "\n\n".join([
            self.policy.render(),
            "【Profile Guidance】\n- " + profile_guidance(normalized_profile),
            narrative.render(),
            character.render(),
            glossary.render(),
            "【Previous Context】\n" + (previous_context.strip() or "無；此段可獨立翻譯。"),
            "【Current Korean Text】\n" + chunk_text,
            "【Output Requirement】\n請直接輸出繁體中文譯文。不要輸出分析、註解、標題或 Markdown。",
        ])

        return LiteraryPromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            narrative_context=narrative,
            character_context=character,
            glossary_context=glossary,
            profile=normalized_profile,
        )

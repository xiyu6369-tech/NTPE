from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping

from core.prompt_compiler import PromptCompiler, PromptSections

from .character_context import CharacterContext
from .glossary_context import GlossaryContext
from .literary_profile import normalize_profile, profile_guidance
from .narrative_context import NarrativeContext
from .prompt_profiler import PromptProfile, build_prompt_profile
from .translation_policy import LiteraryTranslationPolicy


@dataclass
class LiteraryPromptResult:
    system_prompt: str
    user_prompt: str
    narrative_context: NarrativeContext
    character_context: CharacterContext
    glossary_context: GlossaryContext
    prompt_profile: PromptProfile
    profile: str
    prompt_compiler: dict

    def to_prompt_dict(self) -> dict:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "prompt_mode": "compact_literary_v6_ter_v1_5",
            "profile": self.profile,
            "prompt_profile": self.prompt_profile.to_dict(),
            "narrative_context": self.narrative_context.to_dict(),
            "character_context": self.character_context.to_dict(),
            "glossary_context": self.glossary_context.to_dict(),
            "prompt_compiler": dict(self.prompt_compiler),
        }


class LiteraryPromptBuilder:
    """Compact literary prompt builder v6.

    v6 keeps TER-v1.4 compression while improving literary polish guidance and keep each request focused on
    the current novel segment.  It sends only matched glossary entries and a
    small set of narrative/character hints.
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

        system_prompt = self.policy.system_identity()
        policy_text = self.policy.render() + "\n【Profile】\n- " + profile_guidance(normalized_profile)
        previous = _compact_previous_context(previous_context)
        context_parts = [narrative.render(), character.render()]
        if previous != "無":
            context_parts.append("【Previous】" + previous)
        context_text = "\n".join(context_parts)
        glossary_text = glossary.render()
        source_text = "【Korean】\n" + chunk_text.strip()
        output_text = "【Output】直出譯文，禁止標題、註解、Markdown。"

        discipline_enabled = os.environ.get("NTPE_PROMPT_DISCIPLINE", "1").strip().lower() not in {"0", "false", "no", "off"}
        compiled = PromptCompiler(discipline_enabled=discipline_enabled).compile(
            PromptSections(
                system=system_prompt,
                policy=policy_text,
                context=context_text,
                glossary=glossary_text,
                source=source_text,
                output=output_text,
            )
        )
        system_prompt = compiled.system_prompt
        user_prompt = compiled.user_prompt
        profiled_policy_text = policy_text
        if compiled.metadata.get("naturalness_policy_enabled"):
            from core.translation_naturalness import render_naturalness_policy
            naturalness_policy = render_naturalness_policy()
            if naturalness_policy:
                profiled_policy_text += "\n" + naturalness_policy
        prompt_profile = build_prompt_profile(
            system_prompt=system_prompt,
            policy_text=profiled_policy_text,
            context_text=context_text,
            glossary_text=glossary_text,
            source_text=source_text,
        )
        return LiteraryPromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            narrative_context=narrative,
            character_context=character,
            glossary_context=glossary,
            prompt_profile=prompt_profile,
            profile=normalized_profile,
            prompt_compiler=compiled.to_metadata(),
        )


def _compact_previous_context(previous_context: str, limit: int = 160) -> str:
    text = " ".join((previous_context or "").split())
    if not text:
        return "無"
    if len(text) <= limit:
        return text
    return text[-limit:]

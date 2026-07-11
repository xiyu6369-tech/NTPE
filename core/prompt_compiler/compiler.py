from __future__ import annotations

from dataclasses import dataclass
import os

from .model import CompiledPrompt, PromptSections


PROMPT_COMPILER_VERSION = "5.5.2-discipline"


@dataclass(frozen=True)
class PromptCompiler:
    """Compile provider-ready prompts using the unified discipline policy boundary."""

    version: str = PROMPT_COMPILER_VERSION
    discipline_enabled: bool = False
    discipline_profile: str = "literary"

    def compile(self, sections: PromptSections) -> CompiledPrompt:
        from core.translation_discipline.engine import TranslationDisciplineEngine

        engine = TranslationDisciplineEngine(profile=self.discipline_profile)
        active_rules = engine.generation_rules(enabled=self.discipline_enabled)
        discipline = engine.render_generation_policy(enabled=self.discipline_enabled)

        optional = list(sections.optional)
        if discipline:
            optional.append(discipline)

        naturalness_enabled = os.getenv("NTPE_NATURALNESS_POLICY", "1").strip().lower() not in {"0", "false", "no", "off"}
        naturalness = ""
        naturalness_rule_count = 0
        if naturalness_enabled:
            from core.translation_naturalness import NATURALNESS_POLICY_VERSION, NATURALNESS_RULES, render_naturalness_policy
            naturalness = render_naturalness_policy()
            naturalness_rule_count = len(NATURALNESS_RULES)
            if naturalness:
                optional.append(naturalness)

        compiled_sections = PromptSections(
            system=sections.system,
            policy=sections.policy,
            context=sections.context,
            glossary=sections.glossary,
            source=sections.source,
            output=sections.output,
            optional=tuple(optional),
        )
        user_prompt = "\n".join(compiled_sections.ordered_user_sections())
        discipline_metadata = engine.metadata(enabled=bool(active_rules))
        return CompiledPrompt(
            system_prompt=sections.system,
            user_prompt=user_prompt,
            compiler_version=self.version,
            section_order=("policy", "context", "glossary", "optional", "source", "output"),
            metadata={
                "mode": "prompt_discipline" if active_rules else "legacy_equivalent",
                "discipline_enabled": bool(active_rules),
                "discipline_rule_codes": [rule.code for rule in active_rules],
                "discipline_rule_count": len(active_rules),
                "naturalness_policy_version": NATURALNESS_POLICY_VERSION if naturalness_enabled else None,
                "naturalness_policy_enabled": naturalness_enabled,
                "naturalness_rule_count": naturalness_rule_count,
                **discipline_metadata,
            },
        )

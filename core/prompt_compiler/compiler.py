from __future__ import annotations

from dataclasses import dataclass

from .model import CompiledPrompt, PromptSections
from .rules import enabled_discipline_rules, render_discipline_block


PROMPT_COMPILER_VERSION = "5.5.2-discipline"


@dataclass(frozen=True)
class PromptCompiler:
    """Compile provider-ready prompts with optional literary discipline rules."""

    version: str = PROMPT_COMPILER_VERSION
    discipline_enabled: bool = False

    def compile(self, sections: PromptSections) -> CompiledPrompt:
        optional = list(sections.optional)
        active_rules = ()
        if self.discipline_enabled:
            active_rules = enabled_discipline_rules()
            discipline = render_discipline_block(active_rules)
            if discipline:
                optional.append(discipline)

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
            },
        )

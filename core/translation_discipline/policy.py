from __future__ import annotations

from collections.abc import Iterable

from core.prompt_compiler.rules import FOUNDATION_DISCIPLINE_RULES

from .rule import DisciplineRule

POLICY_VERSION = "6.0.0-stage02"

_CATEGORIES = {
    "NO_ADDED_PLOT": "hallucination",
    "NO_ADDED_TRANSITION": "hallucination",
    "NO_ADDED_PSYCHOLOGY": "hallucination",
    "NO_SUMMARIZATION": "completeness",
    "PRESERVE_INFORMATION_ORDER": "chronology",
    "PRESERVE_PARAGRAPH_INTENT": "narrative",
    "NO_PREVIOUS_RESTATEMENT": "repetition",
    "PREVIOUS_CONTEXT_ONLY": "fidelity",
}
_PROFILES = (
    "strict_fidelity",
    "literary_balanced",
    "historical_literary",
    "modern_literary",
    "dialogue_heavy",
    "narration_heavy",
)


def legacy_prompt_discipline_rules() -> tuple[DisciplineRule, ...]:
    return tuple(
        DisciplineRule(
            code=rule.code,
            category=_CATEGORIES.get(rule.code, rule.category),
            title=rule.code.replace("_", " ").title(),
            instruction=rule.instruction,
            phase="generation",
            enabled=rule.enabled_by_default,
            retry_relevant=True,
            evidence_required=True,
            profiles=_PROFILES,
            metadata={
                "legacy_module": "core.prompt_compiler.rules",
                "legacy_code": rule.code,
                "policy_version": POLICY_VERSION,
            },
        )
        for rule in FOUNDATION_DISCIPLINE_RULES
    )


def render_generation_policy(rules: Iterable[DisciplineRule]) -> str:
    """Render the canonical generation policy while preserving v5.5.2 text exactly."""
    selected = tuple(rule for rule in rules if rule.enabled and rule.phase == "generation")
    if not selected:
        return ""
    lines = ["【翻譯紀律】"]
    lines.extend(f"- {rule.instruction}" for rule in selected)
    return "\n".join(lines)

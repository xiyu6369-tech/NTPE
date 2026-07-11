from __future__ import annotations

from collections.abc import Iterable

from core.prompt_compiler.rules import FOUNDATION_DISCIPLINE_RULES

from .rule import DisciplineRule

POLICY_VERSION = "6.0.0-stage02"
VOICE_REGISTER_DISCIPLINE_VERSION = "6.0.0-stage12.4.1"

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


def voice_register_discipline_rules() -> tuple[DisciplineRule, ...]:
    """Stage 12.4.1 feedback-only rules; never added to generation prompts."""
    definitions = (
        ("CHARACTER_VOICE_CONSISTENCY", "characterization", "Character Voice Consistency", "保持同一角色在相同關係與情境中的口吻一致。"),
        ("HONORIFIC_REGISTER_CONSISTENCY", "characterization", "Honorific Register Consistency", "保持稱呼與敬語層級符合人物身分及關係。"),
        ("RELATIONSHIP_DISTANCE_CONSISTENCY", "characterization", "Relationship Distance Consistency", "保持人物關係距離，不自行拉近或疏遠。"),
        ("NARRATIVE_VIEWPOINT_CONSISTENCY", "narrative", "Narrative Viewpoint Consistency", "保持原文敘事人稱、視角與敘事距離。"),
        ("NARRATIVE_REGISTER_CONSISTENCY", "narrative", "Narrative Register Consistency", "保持同一場景敘述語域一致。"),
        ("ERA_REGISTER_CONSISTENCY", "naturalness", "Era Register Consistency", "選詞須符合故事時代、地區與人物身分。"),
        ("DIALOGUE_NARRATION_SEPARATION", "narrative", "Dialogue Narration Separation", "維持人物台詞與旁白的語氣及功能界線。"),
    )
    return tuple(
        DisciplineRule(
            code=code, category=category, title=title, instruction=instruction,
            severity="medium", phase="adaptive_retry", enabled=False,
            retry_relevant=True, locally_repairable=False, evidence_required=True,
            profiles=_PROFILES,
            metadata={"policy_version": VOICE_REGISTER_DISCIPLINE_VERSION,
                      "source": "voice_register_guard", "non_blocking": True,
                      "feedback_only": True},
        )
        for code, category, title, instruction in definitions
    )


def unified_discipline_rules() -> tuple[DisciplineRule, ...]:
    return legacy_prompt_discipline_rules() + voice_register_discipline_rules()


def render_generation_policy(rules: Iterable[DisciplineRule]) -> str:
    """Render the canonical generation policy while preserving v5.5.2 text exactly."""
    selected = tuple(rule for rule in rules if rule.enabled and rule.phase == "generation")
    if not selected:
        return ""
    lines = ["【翻譯紀律】"]
    lines.extend(f"- {rule.instruction}" for rule in selected)
    return "\n".join(lines)

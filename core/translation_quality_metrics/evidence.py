from __future__ import annotations

from core.translation_quality_defects import TranslationDefect

DIMENSION_CATEGORIES = {
    "naturalness": frozenset({"lexical_choice", "narrative_naturalness", "dialogue_naturalness", "chinese_fluency"}),
    "fidelity": frozenset({"semantic_mistranslation", "semantic_precision", "omission", "addition", "under_translation", "over_translation", "action_intensity", "unsupported_detail"}),
    "completeness": frozenset({"omission", "addition", "under_translation", "over_translation"}),
    "narrative": frozenset({"narrative_naturalness", "tone_consistency"}),
    "dialogue": frozenset({"dialogue_naturalness", "honorific"}),
    "terminology": frozenset({"terminology", "character_consistency"}),
    "consistency": frozenset({"character_consistency", "tone_consistency", "style_consistency", "context_continuity"}),
    "traditional_chinese_style": frozenset({"traditional_chinese_style"}),
    "readability": frozenset({"chinese_fluency", "grammar", "lexical_choice"}),
}


def defects_for_dimension(dimension: str, defects: tuple[TranslationDefect, ...]) -> tuple[TranslationDefect, ...]:
    categories = DIMENSION_CATEGORIES[dimension]
    return tuple(row for row in defects if categories.intersection({row.category, *row.secondary_categories}) or dimension in row.metadata.get("dimensions", ()))

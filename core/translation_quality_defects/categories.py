from __future__ import annotations

DEFECT_CATEGORIES = (
    "lexical_choice", "semantic_mistranslation", "semantic_precision", "omission",
    "addition", "under_translation", "over_translation", "narrative_naturalness",
    "dialogue_naturalness", "chinese_fluency", "grammar", "terminology",
    "character_consistency", "tone_consistency", "style_consistency",
    "traditional_chinese_style", "context_continuity", "action_intensity",
    "honorific", "unsupported_detail",
)
DEFECT_CATEGORY_SET = frozenset(DEFECT_CATEGORIES)


def validate_category(value: str) -> str:
    if value not in DEFECT_CATEGORY_SET:
        raise ValueError(f"unsupported defect category: {value}")
    return value

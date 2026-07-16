from __future__ import annotations

from .models import QualityRule

CATEGORIES = ("source_residue", "name_consistency", "subject_reference", "pronoun_reference", "honorific_consistency", "register_consistency", "dialogue_format", "target_script_consistency", "literal_translation_risk", "omission_risk", "addition_risk", "ambiguity_preservation", "era_context_consistency", "glossary_consistency")


def build_quality_rules(language: str, literal_risks: tuple[str, ...]) -> tuple[QualityRule, ...]:
    rules = []
    for category in CATEGORIES:
        blocking = category not in {"literal_translation_risk", "register_consistency", "era_context_consistency"}
        description = f"{language} profile rule for {category.replace('_', ' ')}"
        if category == "literal_translation_risk": description += ": " + ", ".join(literal_risks)
        rules.append(QualityRule(f"{language}-{category.replace('_', '-')}", "1.0", language, "blocking" if blocking else "review", blocking, ("explicit_structural_evidence",), description, f"{language}->zh-Hant"))
    return tuple(rules)

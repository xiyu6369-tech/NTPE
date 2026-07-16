from __future__ import annotations

from .models import NameHandlingPolicy, TargetLanguageRules

COMMON_TARGET_POLICY = TargetLanguageRules(
    language="zh-Hant",
    script="Traditional Han",
    dialogue_quotes="「」",
    requirements=(
        "traditional_chinese", "no_simplified_residue", "no_unapproved_source_residue",
        "no_omission", "no_addition", "no_summary", "no_arbitrary_rewrite",
        "preserve_subject_pronoun_number_time_negation_causality_relationship",
        "preserve_deliberate_ambiguity", "consistent_names_and_terms",
        "no_full_name_completion", "era_culture_voice_sensitive_wording",
        "remove_translationese_without_semantic_change",
    ),
    force_taiwan_terms=False,
    preserve_era_context=True,
)

COMMON_NAME_POLICY = dict(
    approved_variant_policy="human-approved glossary or memory has priority",
    unknown_name_policy="unresolved_or_manual_review",
    nickname_policy="preserve distinct identity unless approved evidence links it",
    full_name_completion_policy="forbidden_without_evidence",
)


def name_policy(*, name_order: str, transliteration_strategy: str, title_policy: str) -> NameHandlingPolicy:
    return NameHandlingPolicy(name_order=name_order, transliteration_strategy=transliteration_strategy, title_policy=title_policy, **COMMON_NAME_POLICY)

from __future__ import annotations

from .common import COMMON_TARGET_POLICY, name_policy
from .models import *
from .quality_rules import build_quality_rules


def build_english_profile() -> LanguageProfile:
    return LanguageProfile(
        "literary-en-zh-hant", "1.0", SCHEMA_VERSION, "en", "zh-Hant", "English Literary to Traditional Chinese", "experimental",
        SourceLanguageRules(False, False, ("pronoun_overrepetition", "passive_literalism", "nominalization_rigidity", "long_sentence_copy", "relative_clause_stacking", "prepositional_literalism", "weak_verb", "overformal_dialogue", "idiom_literalism", "phrasal_verb_mistranslation"), ("past", "present", "future", "perfect", "progressive", "conditional", "subjunctive"), ("singular they does not prove gender", "you number and honorific may be unresolved")),
        COMMON_TARGET_POLICY,
        name_policy(name_order="given_family", transliteration_strategy="approved_transliteration_only", title_policy="era-rank-setting-sensitive"),
        PronounPolicy(False, False, "strong_but_identity_bound", ("he_she_they_it_preserve_identity", "singular_they_no_gender_assignment", "you_number_and_register_may_remain_unresolved"), "preserve_unresolved", True, "selected human-approved evidence only"),
        HonorificPolicy(("Mr.", "Mrs.", "Ms.", "Dr.", "Sir", "Lady"), ("formal", "neutral", "informal", "intimate", "hostile"), ("rank", "distance", "setting"), ("contextual Chinese title", "approved transliteration", "selective omission if identity retained"), ("always_use_您", "modernize_historical_title", "merge_alias_with_canonical_identity")),
        DialoguePolicy(('"', "'"), "normalize to 「」", "use 『』", "preserve continuation", "preserve dash or ellipsis interruption", "never complete", "explicit tag or unresolved", True),
        NarrativePolicy("work metadata controls historical fantasy modern context", "foreign terms may preserve translate transliterate or annotate", "preserve focal distance", ("character-specific", "narrative-present-aware"), "metadata-versioned", "never force modern colloquial Chinese", "never force Taiwan-local vocabulary"),
        ResidueDetectionPolicy(("Latin",), (r"[A-Za-z]+(?:\s+[A-Za-z]+){2,}", r"\{\{[^}]+\}\}"), ("approved_name", "brand", "abbreviation", "work_title", "code", "foreign_dialogue"), True),
        SemanticHintPolicy((r"(?:Mr\.|Mrs\.|Ms\.|Dr\.|Sir|Lady)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",), (r"\d+(?:\.\d+)?",), ("yesterday", "today", "tomorrow", "before", "after"), ("not", "never", "no", "cannot"), ("may", "might", "could", "should", "must", "would"), ("because", "therefore", "if", "although", "but"), ('"',), ("Mr.", "Mrs.", "Ms.", "Dr.", "Sir", "Lady"), ("someone", "some", "several", "perhaps", "maybe"), False),
        build_quality_rules("en", ("passive_literalism", "idiom_literalism", "phrasal_verb_mistranslation")),
        "2026-07-16T00:00:00Z", "2026-07-16T00:00:00Z", "",
    )

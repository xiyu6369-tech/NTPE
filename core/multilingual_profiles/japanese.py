from __future__ import annotations

from .common import COMMON_TARGET_POLICY, name_policy
from .models import *
from .quality_rules import build_quality_rules


def build_japanese_profile() -> LanguageProfile:
    return LanguageProfile(
        "literary-ja-zh-hant", "1.0", SCHEMA_VERSION, "ja", "zh-Hant", "Japanese Literary to Traditional Chinese", "experimental",
        SourceLanguageRules(True, True, ("topic_subject_confusion", "adversative_passive", "causative", "giving_receiving_agent", "omitted_object", "long_modifier", "onomatopoeia", "sentence_final_voice", "false_friend_kanji", "loanword_literalism"), ("event_order_and_aspect_must_survive",), ("first-person form alone does not prove gender",)),
        COMMON_TARGET_POLICY,
        name_policy(name_order="family_given", transliteration_strategy="approved_variant_or_manual_review", title_policy="honorific-relationship-era-sensitive"),
        PronounPolicy(True, True, "medium", ("私_僕_俺_あたし_わたくし_are_voice_evidence_not_gender_proof", "君_あなた_お前_貴様_require_relationship_context"), "preserve_unresolved", True, "selected human-approved evidence only"),
        HonorificPolicy(("さん", "様", "君", "ちゃん", "ございます", "いたします", "なさる"), ("尊敬語", "謙讓語", "丁寧語", "普通體"), ("distance", "power", "in_group_out_group"), ("Chinese voice", "contextual title", "selective honorific rendering"), ("always_use_您", "always_use_請", "change_agent_for_humble_or_respectful", "erase_register_shift")),
        DialoguePolicy(("「」", "『』", "\""), "normalize to 「」", "preserve 『』 nesting", "preserve continuation", "preserve interruption", "never complete", "explicit evidence or unresolved", True),
        NarrativePolicy("work metadata controls era", "Japanese cultural terms may preserve translate transliterate or annotate", "preserve source distance", ("character-specific", "sentence-final voice aware"), "metadata-versioned", "never force modern colloquial Chinese", "never localize foreign setting to Taiwan"),
        ResidueDetectionPolicy(("Hiragana", "Katakana"), (r"[ぁ-ん]+", r"[ァ-ヶー]+", r"(?:は|が|を|に|で|と|へ)$"), ("approved_name", "brand", "work_title", "foreign_dialogue"), True),
        SemanticHintPolicy((r"[\u4e00-\u9fff]{1,4}(?:さん|様|君|ちゃん)?",), (r"\d+", r"[一二三四五六七八九十百千]+"), ("昨日", "今日", "明日", "前", "後"), ("ない", "ぬ", "ず", "ません"), ("かもしれない", "だろう", "べき", "はず"), ("から", "ので", "だから", "しかし", "もし"), ("「", "」", "『", "』"), ("さん", "様", "君", "ちゃん"), ("誰か", "ある", "いくつか", "かもしれない"), True),
        build_quality_rules("ja", ("topic_subject_confusion", "giving_receiving_agent", "false_friend_kanji", "loanword_literalism")),
        "2026-07-16T00:00:00Z", "2026-07-16T00:00:00Z", "",
    )

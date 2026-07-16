from __future__ import annotations

from .common import COMMON_TARGET_POLICY, name_policy
from .models import *
from .quality_rules import build_quality_rules


def build_korean_profile() -> LanguageProfile:
    return LanguageProfile(
        "literary-ko-zh-hant", "1.0", SCHEMA_VERSION, "ko", "zh-Hant", "Korean Literary to Traditional Chinese", "experimental",
        SourceLanguageRules(True, True, ("subject_omission", "object_omission", "long_adnominal_literalism", "ending_literalism", "connector_overretention", "passive_causative_rigidity", "mechanical_honorific", "relationship_title_mistranslation"), ("explicit_time_relations_must_survive",), ("honorific ending is not identity evidence",)),
        COMMON_TARGET_POLICY,
        name_policy(name_order="family_given", transliteration_strategy="approved_transliteration_only", title_policy="relationship-era-scene-sensitive"),
        PronounPolicy(True, True, "weak", ("omission_does_not_resolve_identity", "multiple_candidates_remain_unresolved"), "preserve_unresolved", True, "selected human-approved evidence only"),
        HonorificPolicy(("-습니다", "-ㅂ니다", "-어요", "-아요", "-시오", "-네", "-오"), ("존댓말", "반말", "하십시오체", "해요체", "해체", "하게체", "하오체"), ("social_distance", "age_or_rank_context"), ("title", "relationship term", "register-preserving Chinese voice"), ("always_use_您", "infer_identity_from_ending", "erase_register_difference")),
        DialoguePolicy(("\"", "‘’", "“”"), "normalize to 「」 without semantic change", "use 『』", "preserve speaker continuity", "preserve interruption", "never complete", "explicit evidence or unresolved", True),
        NarrativePolicy("work metadata may select ancient modern fantasy or other", "Korean cultural terms may preserve translate transliterate or annotate", "preserve source distance", ("character-specific", "scene-sensitive"), "metadata-versioned", "never force modern colloquial Chinese", "never force Taiwan-local titles"),
        ResidueDetectionPolicy(("Hangul",), (r"[가-힣]+", r"(?:은|는|이|가|을|를|에게|에서)$"), ("approved_name", "brand", "work_title", "foreign_dialogue"), True),
        SemanticHintPolicy((r"[가-힣]{2,4}(?:씨|님)?",), (r"\d+", r"[일이삼사오육칠팔구십백천]+"), ("어제", "오늘", "내일", "후", "전"), ("안", "못", "없", "아니"), ("수 있다", "수 없다", "것 같다", "아마"), ("때문에", "그래서", "그러나", "만약"), ('"', "“", "”"), ("님", "씨", "선배", "후배"), ("누군가", "어느", "몇", "아마"), True),
        build_quality_rules("ko", ("long_adnominal_literalism", "ending_literalism", "mechanical_honorific")),
        "2026-07-16T00:00:00Z", "2026-07-16T00:00:00Z", "",
    )

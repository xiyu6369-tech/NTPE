from __future__ import annotations

import re
from dataclasses import fields

from .models import LanguageProfile, SCHEMA_VERSION
from .quality_rules import CATEGORIES

SUPPORTED_SOURCES = ("ko", "ja", "en")
TARGET_LANGUAGE = "zh-Hant"
STATUSES = ("active", "experimental", "deprecated", "frozen")


def validate_language_profile(profile: LanguageProfile) -> None:
    if profile.schema_version != SCHEMA_VERSION: raise ValueError("unknown schema version")
    if profile.source_language not in SUPPORTED_SOURCES or profile.target_language != TARGET_LANGUAGE: raise ValueError("invalid language pair")
    if profile.profile_version != "1.0": raise ValueError("unknown profile version")
    if profile.status not in STATUSES: raise ValueError("invalid profile status")
    if profile.name_policy.full_name_completion_policy != "forbidden_without_evidence": raise ValueError("unsafe full name policy")
    if profile.name_policy.transliteration_strategy == "automatic_transliteration": raise ValueError("automatic transliteration forbidden")
    if profile.target_rules is None or profile.semantic_hints is None or profile.residue_policy is None: raise ValueError("missing required policy")
    categories = {rule.rule_id.removeprefix(profile.source_language + "-").replace("-", "_") for rule in profile.quality_rules}
    if not set(CATEGORIES) <= categories: raise ValueError("missing quality rule")
    if not re.fullmatch(r"[0-9a-f]{64}", profile.fingerprint): raise ValueError("invalid fingerprint")


def validate_registry(profiles: tuple[LanguageProfile, ...]) -> None:
    active = set()
    for profile in profiles:
        validate_language_profile(profile)
        if profile.status == "active":
            pair = (profile.source_language, profile.target_language)
            if pair in active: raise ValueError("duplicate active profile")
            active.add(pair)

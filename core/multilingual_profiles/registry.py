from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from functools import lru_cache

from .english import build_english_profile
from .japanese import build_japanese_profile
from .korean import build_korean_profile
from .models import LanguageProfile, LanguageProfileIdentity
from .validation import validate_language_profile, validate_registry

IDENTITY_EXCLUDED_FIELDS = ("display_name", "status", "created_at", "updated_at", "fingerprint")


def _canonical(value) -> str: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=128)
def build_language_profile_fingerprint(profile: LanguageProfile) -> str:
    value = asdict(profile)
    for key in IDENTITY_EXCLUDED_FIELDS: value.pop(key, None)
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _finalize(profile: LanguageProfile) -> LanguageProfile:
    return replace(profile, fingerprint=build_language_profile_fingerprint(profile))


_PROFILES = tuple(_finalize(builder()) for builder in (build_korean_profile, build_japanese_profile, build_english_profile))
validate_registry(_PROFILES)


def list_language_profiles() -> tuple[LanguageProfile, ...]: return _PROFILES


def get_language_profile(profile_id: str, version: str = "1.0") -> LanguageProfile:
    for profile in _PROFILES:
        if profile.profile_id == profile_id and profile.profile_version == version: return profile
    raise LookupError("profile not found or version mismatch")


def build_language_profile_identity(profile: LanguageProfile) -> LanguageProfileIdentity:
    validate_language_profile(profile)
    return LanguageProfileIdentity(profile.profile_id, profile.profile_version, profile.source_language, profile.target_language, profile.fingerprint)

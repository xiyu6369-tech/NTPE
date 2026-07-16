from __future__ import annotations

from dataclasses import asdict

from .models import LanguageProfile
from .validation import validate_language_profile


def build_semantic_verification_hints(profile: LanguageProfile) -> dict:
    validate_language_profile(profile)
    return {"profile_id": profile.profile_id, "profile_version": profile.profile_version, "profile_fingerprint": profile.fingerprint, "origin": "rule_derived", "verification_authority": "LCR Batch 6", "can_decide_pass": False, "hints": asdict(profile.semantic_hints)}

from __future__ import annotations

import re
from dataclasses import asdict

from .models import LanguageProfile
from .registry import build_language_profile_identity
from .validation import validate_language_profile


def detect_source_residue(text: str, profile: LanguageProfile, *, allowed_terms: tuple[str, ...] = ()) -> tuple[dict, ...]:
    validate_language_profile(profile)
    findings = []
    for pattern, script in zip(profile.residue_policy.patterns, profile.residue_policy.scripts + profile.residue_policy.scripts):
        for match in re.finditer(pattern, text):
            value = match.group(0)
            allowed = value in allowed_terms or (profile.source_language == "en" and (re.fullmatch(r"[A-Z][a-z]+", value) or re.fullmatch(r"[A-Z]{2,5}", value)))
            findings.append({"text": value, "scope": [match.start(), match.end()], "script": script, "confidence": 1.0, "allowed_by_policy": bool(allowed), "blocking": profile.residue_policy.blocking_default and not allowed, "reason": "allowlisted literary content" if allowed else "unprocessed source-language residue"})
    unique = {(x["scope"][0], x["scope"][1], x["text"]): x for x in findings}
    return tuple(unique[key] for key in sorted(unique))


def build_character_memory_hints(profile: LanguageProfile) -> dict:
    return {"profile_identity": asdict(build_language_profile_identity(profile)), "origin": "rule_derived", "creates_approved_memory": False, "human_approved_priority": True, "gender_inference_confirmed": False, "name_policy": asdict(profile.name_policy), "pronoun_policy": asdict(profile.pronoun_policy)}


def build_context_scene_hints(profile: LanguageProfile) -> dict:
    return {"profile_identity": asdict(build_language_profile_identity(profile)), "origin": "rule_derived", "forces_reference_resolution": False, "scene_memory_remains_authority": True, "speaker_markers": profile.semantic_hints.dialogue_markers, "temporal_markers": profile.semantic_hints.time_patterns}


def build_cache_profile_identity(profile: LanguageProfile) -> dict:
    identity = build_language_profile_identity(profile)
    return {"language_profile_id": identity.profile_id, "language_profile_version": identity.profile_version, "language_profile_fingerprint": identity.fingerprint, "source_language": identity.source_language, "target_language": identity.target_language}


def build_polish_profile_view(profile: LanguageProfile) -> dict:
    trigger_types = (f"{profile.source_language}:translationese", f"{profile.source_language}:register_mismatch", f"{profile.source_language}:honorific_mismatch", f"{profile.source_language}:dialogue_naturalness", f"{profile.source_language}:era_context_mismatch")
    return {"profile_identity": build_cache_profile_identity(profile), "trigger_types": trigger_types, "trigger_is_semantic_approval": False, "provider_state_controlled": False, "production_integrated": False}


def build_verification_profile_identity(profile: LanguageProfile) -> dict:
    return {**build_cache_profile_identity(profile), "profile_can_accept_polish": False, "verification_authority": "LCR Batch 6", "fail_closed_threshold_lowered": False}

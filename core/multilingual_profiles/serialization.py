from __future__ import annotations

import json
from dataclasses import asdict

from .models import *
from .registry import build_language_profile_fingerprint
from .validation import validate_language_profile


def serialize_language_profile(profile: LanguageProfile) -> str:
    validate_language_profile(profile)
    return json.dumps(asdict(profile), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reject(value) -> None:
    text = repr(value).lower()
    if "../" in text or "..\\" in text: raise ValueError("path traversal rejected")
    if any(x in text for x in ("authorization: bearer", "raw_provider_request", "raw_provider_response", "private key")): raise ValueError("unsafe payload")


def deserialize_language_profile(payload: str) -> LanguageProfile:
    try: value = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc: raise ValueError("malformed JSON") from exc
    _reject(value)
    def tuples(mapping):
        return {key: tuple(item) if isinstance(item, list) else item for key, item in mapping.items()}
    try:
        profile = LanguageProfile(
            profile_id=value["profile_id"], profile_version=value["profile_version"], schema_version=value["schema_version"], source_language=value["source_language"], target_language=value["target_language"], display_name=value["display_name"], status=value["status"],
            source_rules=SourceLanguageRules(**tuples(value["source_rules"])), target_rules=TargetLanguageRules(**tuples(value["target_rules"])), name_policy=NameHandlingPolicy(**tuples(value["name_policy"])), pronoun_policy=PronounPolicy(**tuples(value["pronoun_policy"])), honorific_policy=HonorificPolicy(**tuples(value["honorific_policy"])), dialogue_policy=DialoguePolicy(**tuples(value["dialogue_policy"])), narrative_policy=NarrativePolicy(**tuples(value["narrative_policy"])), residue_policy=ResidueDetectionPolicy(**tuples(value["residue_policy"])), semantic_hints=SemanticHintPolicy(**tuples(value["semantic_hints"])), quality_rules=tuple(QualityRule(**tuples(x)) for x in value["quality_rules"]), created_at=value["created_at"], updated_at=value["updated_at"], fingerprint=value["fingerprint"])
    except (KeyError, TypeError) as exc: raise ValueError("missing required profile section") from exc
    validate_language_profile(profile)
    if build_language_profile_fingerprint(profile) != profile.fingerprint: raise ValueError("profile fingerprint mismatch")
    return profile

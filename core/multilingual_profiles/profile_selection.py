from __future__ import annotations

from .models import LanguageProfileSelection
from .registry import list_language_profiles
from .validation import SUPPORTED_SOURCES, TARGET_LANGUAGE


def select_language_profile(source_language: str, target_language: str, *, requested_profile_id: str | None = None, requested_version: str | None = None) -> LanguageProfileSelection:
    if not isinstance(source_language, str) or not isinstance(target_language, str): return LanguageProfileSelection("invalid", None, "language codes must be strings")
    if source_language not in SUPPORTED_SOURCES or target_language != TARGET_LANGUAGE: return LanguageProfileSelection("unsupported_pair", None, "no fallback is allowed")
    pair = [p for p in list_language_profiles() if p.source_language == source_language and p.target_language == target_language]
    if requested_profile_id and all(p.profile_id != requested_profile_id for p in pair): return LanguageProfileSelection("not_found", None, "requested profile does not match pair")
    pair = [p for p in pair if not requested_profile_id or p.profile_id == requested_profile_id]
    if requested_version and all(p.profile_version != requested_version for p in pair): return LanguageProfileSelection("version_mismatch", None, "requested version unavailable")
    pair = [p for p in pair if not requested_version or p.profile_version == requested_version]
    return LanguageProfileSelection("selected", pair[0], "exact deterministic pair match") if len(pair) == 1 else LanguageProfileSelection("not_found", None, "profile not found")

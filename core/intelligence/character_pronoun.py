# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Dict, Iterable, List

PRONOUNS = ("他", "她", "他們", "她們", "對方", "那個男人", "那個女人", "哥哥", "弟弟", "姐姐", "妹妹")


def detect_pronouns(text: str) -> List[str]:
    return [pronoun for pronoun in PRONOUNS if pronoun in text]


def resolve_pronouns(text: str, recent_characters: Iterable[str]) -> Dict[str, str]:
    candidates = [name for name in recent_characters if name]
    if not candidates:
        return {}
    fallback = candidates[-1]
    return {pronoun: fallback for pronoun in detect_pronouns(text)}

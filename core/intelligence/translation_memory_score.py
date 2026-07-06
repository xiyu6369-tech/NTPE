# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable

from .translation_memory_entry import normalize_memory_text


def lexical_similarity(left: str, right: str) -> float:
    left_norm = normalize_memory_text(left)
    right_norm = normalize_memory_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def token_overlap(left: Iterable[str], right: Iterable[str]) -> float:
    lset = {x for x in left if x}
    rset = {x for x in right if x}
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)

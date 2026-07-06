# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple


def build_alias_index(entries: Dict[str, Iterable[str]]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for canonical, aliases in entries.items():
        index[canonical] = canonical
        for alias in aliases:
            if alias:
                index[alias] = canonical
    return index


def detect_alias_conflicts(entries: Dict[str, Iterable[str]]) -> List[Tuple[str, str, str]]:
    seen: Dict[str, str] = {}
    conflicts: List[Tuple[str, str, str]] = []
    for canonical, aliases in entries.items():
        for alias in [canonical, *list(aliases)]:
            owner = seen.get(alias)
            if owner and owner != canonical:
                conflicts.append((alias, owner, canonical))
            seen[alias] = canonical
    return conflicts

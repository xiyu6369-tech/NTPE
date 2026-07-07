from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class LockedTerm:
    source: str
    target: str
    term_type: str = "term"
    immutable: bool = True


def _term_type(source: str) -> str:
    # Korean Hangul name-like entries are treated as character/name locks.
    if any("가" <= ch <= "힣" for ch in source):
        return "name"
    return "term"


@dataclass
class GlossaryContext:
    matched_terms: list[LockedTerm] = field(default_factory=list)
    alias_map: dict[str, str] = field(default_factory=dict)
    max_terms: int = 24
    max_aliases: int = 18

    @classmethod
    def from_locked_dictionary(
        cls,
        locked_dictionary: Mapping[str, str],
        chunk_text: str,
        alias_map: Mapping[str, str] | None = None,
        *,
        max_terms: int = 24,
        max_aliases: int = 18,
    ) -> "GlossaryContext":
        # Dynamic glossary: only terms appearing in the current chunk are sent.
        matched: list[LockedTerm] = []
        for src, target in locked_dictionary.items():
            if src and target and src in chunk_text:
                matched.append(LockedTerm(source=src, target=target, term_type=_term_type(src)))
        # Prefer longer source terms first because they are usually more specific.
        matched.sort(key=lambda t: (-len(t.source), t.source))
        limited = matched[:max_terms]

        useful_aliases: dict[str, str] = {}
        for alias, target in (alias_map or {}).items():
            if target and any(term.target == target for term in limited):
                useful_aliases[alias] = target
            if len(useful_aliases) >= max_aliases:
                break
        return cls(matched_terms=limited, alias_map=useful_aliases, max_terms=max_terms, max_aliases=max_aliases)

    def render(self) -> str:
        if not self.matched_terms:
            return "【Glossary】\n- 無"
        terms = "\n".join(f"- {t.source} => {t.target}" for t in self.matched_terms)
        if not self.alias_map:
            return f"【Glossary】\n{terms}"
        aliases = "\n".join(f"- {alias} => {target}" for alias, target in sorted(self.alias_map.items()))
        return f"【Glossary】\n{terms}\n【Forbidden Aliases】\n{aliases}"

    def to_dict(self) -> dict:
        return {
            "matched_terms": [term.__dict__ for term in self.matched_terms],
            "alias_map": self.alias_map,
            "max_terms": self.max_terms,
            "max_aliases": self.max_aliases,
        }

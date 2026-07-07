from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class LockedTerm:
    source: str
    target: str
    term_type: str = "term"
    immutable: bool = True


@dataclass
class GlossaryContext:
    matched_terms: list[LockedTerm] = field(default_factory=list)
    alias_map: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_locked_dictionary(cls, locked_dictionary: Mapping[str, str], chunk_text: str, alias_map: Mapping[str, str] | None = None) -> "GlossaryContext":
        matched = []
        for src, target in locked_dictionary.items():
            if src and target and src in chunk_text:
                term_type = "character" if any(ch in src for ch in "정카일태의") else "term"
                matched.append(LockedTerm(source=src, target=target, term_type=term_type))
        return cls(matched_terms=matched, alias_map=dict(alias_map or {}))

    def render(self) -> str:
        if not self.matched_terms:
            terms = "- 無"
        else:
            terms = "\n".join(
                f"- {term.source} → {term.target}（type={term.term_type}, immutable={str(term.immutable).lower()}）"
                for term in self.matched_terms
            )
        aliases = "\n".join(
            f"- 禁止使用「{alias}」，必須改為「{target}」" for alias, target in sorted(self.alias_map.items())
        ) or "- 無"
        return f"【Locked Glossary】\n{terms}\n\n【Forbidden Alias Corrections】\n{aliases}"

    def to_dict(self) -> dict:
        return {
            "matched_terms": [term.__dict__ for term in self.matched_terms],
            "alias_map": self.alias_map,
        }

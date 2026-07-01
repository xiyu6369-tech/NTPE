"""Foundation-08.6 semantic ranking helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

from ..contracts import KnowledgeItem


@dataclass
class KnowledgeSearchResult:
    """Search result envelope with ranking metadata."""

    item: KnowledgeItem
    score: float
    matched_tokens: List[str]
    metadata: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item": self.item.to_dict(),
            "score": self.score,
            "matched_tokens": list(self.matched_tokens),
            "metadata": dict(self.metadata or {}),
        }


class KnowledgeRankingEngine:
    """Deterministic hybrid ranking used before vector backends exist."""

    version = "foundation-08.6"

    def score(self, query_tokens: Iterable[str], item_tokens: Iterable[str], item: KnowledgeItem | None = None, query_text: str = "") -> tuple[float, List[str]]:
        query_set: Set[str] = set(query_tokens)
        item_set: Set[str] = set(item_tokens)
        if not query_set:
            return 0.0, []
        matched = sorted(query_set.intersection(item_set))
        if not matched:
            return 0.0, []
        token_score = len(matched) / max(len(query_set), 1)
        coverage_score = len(matched) / max(len(item_set), 1)
        exact_bonus = 0.0
        if item is not None and query_text:
            haystack = f"{item.key} {item.value} {item.domain}".lower()
            if query_text.lower() in haystack:
                exact_bonus = 0.25
        return round(token_score + coverage_score + exact_bonus, 6), matched

    def rank(self, results: Iterable[KnowledgeSearchResult], limit: int | None = None) -> List[KnowledgeSearchResult]:
        ranked = sorted(results, key=lambda result: (-result.score, result.item.domain, result.item.key))
        return ranked[:limit] if limit is not None else ranked


__all__ = ["KnowledgeRankingEngine", "KnowledgeSearchResult"]

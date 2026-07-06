# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence

from .translation_memory_entry import TranslationMemoryEntry
from .translation_memory_index import memory_tokens
from .translation_memory_policy import TranslationMemoryPolicy
from .translation_memory_result import TranslationMemoryMatch
from .translation_memory_score import lexical_similarity, token_overlap
from .translation_memory_store import TranslationMemoryStore


class TranslationMemoryMatcher:
    def __init__(self, policy: TranslationMemoryPolicy | None = None) -> None:
        self.policy = policy or TranslationMemoryPolicy()

    def match(
        self,
        store: TranslationMemoryStore,
        query: str,
        *,
        domain: str = "general",
        target_language: str = "zh-TW",
        context_tags: Sequence[str] | None = None,
        terminology: Mapping[str, str] | None = None,
        character_refs: Sequence[str] | None = None,
    ) -> List[TranslationMemoryMatch]:
        exact_id = store.index.exact(query)
        candidate_ids = set(store.index.candidates(query))
        if exact_id:
            candidate_ids.add(exact_id)
        if not candidate_ids and len(store) <= 200:
            candidate_ids.update(entry.entry_id or "" for entry in store)

        matches: List[TranslationMemoryMatch] = []
        for entry_id in candidate_ids:
            entry = store.get(entry_id)
            if entry is None:
                continue
            match = self._score_entry(entry, query, domain, target_language, context_tags or [], terminology or {}, character_refs or [], exact=(entry_id == exact_id))
            if match.score >= self.policy.min_score or match.match_type == "exact":
                matches.append(match)
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[: self.policy.max_matches]

    def _score_entry(self, entry: TranslationMemoryEntry, query: str, domain: str, target_language: str, context_tags: Iterable[str], terminology: Mapping[str, str], character_refs: Iterable[str], *, exact: bool) -> TranslationMemoryMatch:
        if exact:
            return TranslationMemoryMatch(entry=entry, score=self.policy.exact_score, match_type="exact", reasons=["exact_source_match"])
        score = lexical_similarity(query, entry.source_text)
        reasons = ["fuzzy_source_match"]
        score += token_overlap(context_tags, entry.context_tags) * self.policy.context_weight
        score += token_overlap(terminology.keys(), entry.terminology.keys()) * self.policy.terminology_weight
        score += token_overlap(character_refs, entry.character_refs) * self.policy.character_weight
        if self.policy.prefer_same_domain and domain == entry.domain:
            score += 0.03
            reasons.append("same_domain")
        if self.policy.prefer_same_target_language and target_language == entry.target_language:
            score += 0.03
            reasons.append("same_target_language")
        match_type = "fuzzy" if score < 0.96 else "near_exact"
        return TranslationMemoryMatch(entry=entry, score=self.policy.clamp_score(score), match_type=match_type, reasons=reasons)

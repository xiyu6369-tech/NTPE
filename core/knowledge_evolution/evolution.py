"""RM-7.0 Knowledge Evolution Foundation — evolution engine.

Detects novel terms during translation output and creates
Learning Candidates for unknown entities — completely offline.
No provider. No network.

The evolution engine:
  1. Scans for unknown source terms in translation output
  2. Creates or reinforces LearningCandidates
  3. Tracks occurrence counts and confidence
  4. Generates EvolutionReport summaries
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .manager import KnowledgeManager
from .models import (
    CandidateStatus,
    EntityType,
    EvolutionReport,
    PriorityLevel,
)


class KnowledgeEvolution:
    """Offline knowledge learning engine.

    Scans for unknown terms and builds candidate knowledge
    without any provider or API calls.
    """

    def __init__(self, manager: KnowledgeManager):
        self._manager = manager
        self._conflicts: List = []

    def learn_term(
        self,
        source: str,
        canonical: str,
        entity_type: EntityType = EntityType.CHARACTER,
        confidence: float = 0.5,
        context_hints: Optional[List[str]] = None,
    ) -> Dict:
        existing = self._manager.resolver.resolve(source)
        if existing is not None:
            return {"status": "exists", "entity": existing.to_dict()}

        existing_candidate = self._manager.resolver.find_candidate(source)
        if existing_candidate is not None:
            boosted = self._manager.add_candidate(
                source=source,
                canonical=canonical,
                entity_type=entity_type,
                confidence=existing_candidate.confidence,
                context_hints=(existing_candidate.context_hints + (context_hints or [])),
            )
            return self._build_result("reinforced", boosted)

        candidate = self._manager.add_candidate(
            source=source,
            canonical=canonical,
            entity_type=entity_type,
            confidence=confidence,
            context_hints=context_hints,
        )
        return self._build_result("new", candidate)

    def verify_term(
        self,
        source: str,
        observed_canonical: str,
        entity_type: EntityType = EntityType.CHARACTER,
    ) -> Optional[Dict]:
        entity = self._manager.resolver.resolve(source)
        if entity is None or entity.canonical == observed_canonical:
            return None

        conflict = self._manager.detect_conflict(source, observed_canonical, entity_type)
        result = {
            "status": "conflict",
            "source": source,
            "expected": entity.canonical,
            "observed": observed_canonical,
            "severity": conflict.severity.value if conflict else "UNKNOWN",
        }
        self._conflicts.append(result)
        return result

    def scan_terms(
        self,
        terms: List[Dict],
        default_type: EntityType = EntityType.CHARACTER,
    ) -> EvolutionReport:
        new_count = 0
        updated_count = 0
        conflict_count = 0

        for term in terms:
            source = term.get("source", "")
            canonical = term.get("canonical", source)
            etype = term.get("entity_type", default_type)
            if isinstance(etype, str):
                try:
                    etype = EntityType(etype)
                except ValueError:
                    etype = default_type

            confidence = term.get("confidence", 0.5)
            context = term.get("context_hints")
            discover = term.get("discover", True)

            if discover:
                result = self.learn_term(
                    source=source,
                    canonical=canonical,
                    entity_type=etype,
                    confidence=confidence,
                    context_hints=context,
                )
                if result["status"] == "new":
                    new_count += 1
                elif result["status"] == "candidate":
                    updated_count += 1

            if term.get("verify", True):
                vresult = self.verify_term(source, canonical, etype)
                if vresult is not None:
                    conflict_count += 1

        return EvolutionReport(
            new_entities=new_count,
            updated_entities=updated_count,
            conflicts=conflict_count,
            total_entities=sum(
                self._manager.store.entity_count(p)
                for p in (PriorityLevel.USER, PriorityLevel.RUNTIME, PriorityLevel.LEARNING)
            ),
            total_candidates=self._manager.store.candidate_count(),
            details={"conflict_samples": self._conflicts[-10:]},
        )

    def promote_all_candidates(
        self,
        min_confidence: float = 0.5,
        min_occurrences: int = 1,
        max_count: int = 100,
    ) -> EvolutionReport:
        candidates = self._manager.list_candidates()
        promoted = 0
        rejected = 0

        for candidate in candidates:
            if candidate.status != CandidateStatus.PENDING:
                continue
            if candidate.confidence >= min_confidence and candidate.occurrence_count >= min_occurrences:
                self._manager.promote_candidate(candidate.source)
                promoted += 1
            else:
                self._manager.reject_candidate(candidate.source)
                rejected += 1

        return EvolutionReport(
            promoted_candidates=promoted,
            rejected_candidates=rejected,
            total_entities=self._manager.store.entity_count(PriorityLevel.LEARNING),
            total_candidates=self._manager.store.candidate_count(),
        )

    @property
    def conflicts(self) -> List:
        return list(self._conflicts)

    def summary(self) -> Dict:
        return {
            "total_entities": self._manager.store.entity_count(PriorityLevel.USER)
            + self._manager.store.entity_count(PriorityLevel.RUNTIME)
            + self._manager.store.entity_count(PriorityLevel.LEARNING),
            "candidates": self._manager.store.candidate_count(),
            "conflicts": len(self._conflicts),
        }

    def _build_result(self, status: str, candidate) -> Dict:
        return {
            "status": status,
            "source": candidate.source,
            "canonical": candidate.canonical,
            "confidence": candidate.confidence,
            "occurrences": getattr(candidate, "occurrence_count", 0),
        }
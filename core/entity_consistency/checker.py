"""RM-7.1 Consistency Checker — compare scanner results against expected forms.

- For every knowledge entry the checker verifies that the canonical
  target form appears in the translation (or identifies a mismatch).
- Fuzzy detection: if the canonical form is missing but a close variant
  is found, a mismatch is reported with severity based on edit distance.
- Never mutates knowledge, glossaries, or translations.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from core.entity_consistency.models import (
    ENTITY_TYPE_TO_CATEGORY,
    REPORTABLE_TYPES,
    EntityMatch,
    EntityMismatch,
    EntityCategory,
)
from core.knowledge_evolution.models import EntityType, Severity

_MIN_SIMILARITY_THRESHOLD: float = 0.60


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _severity_from_distance(similarity: float) -> Severity:
    if similarity >= 0.90:
        return Severity.LOW
    if similarity >= 0.75:
        return Severity.MEDIUM
    return Severity.HIGH


class ConsistencyChecker:
    """Compare expected canonical forms against translation text."""

    def __init__(self) -> None:
        self._matches: List[EntityMatch] = []
        self._mismatches: List[EntityMismatch] = []

    def clear(self) -> None:
        self._matches.clear()
        self._mismatches.clear()

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def check_one(
        self,
        source: str,
        expected: str,
        translated_text: str,
        entity_type: EntityType,
        knowledge_id: Optional[str] = None,
    ) -> Optional[EntityMismatch]:
        if not expected:
            return None

        pos = translated_text.find(expected)
        if pos != -1:
            match = EntityMatch(
                source=source,
                expected=expected,
                found=expected,
                entity_type=entity_type,
                position=pos,
            )
            self._matches.append(match)
            return None

        best_match, best_score, best_pos = self._find_best_variant(
            expected, translated_text
        )

        if best_match and best_score >= _MIN_SIMILARITY_THRESHOLD:
            mismatch = EntityMismatch(
                source=source,
                expected=expected,
                found=best_match,
                entity_type=entity_type,
                severity=_severity_from_distance(best_score),
                position=best_pos,
                knowledge_id=knowledge_id,
            )
            self._mismatches.append(mismatch)
            return mismatch

        mismatch = EntityMismatch(
            source=source,
            expected=expected,
            found="",
            entity_type=entity_type,
            severity=Severity.HIGH,
            knowledge_id=knowledge_id,
        )
        self._mismatches.append(mismatch)
        return mismatch

    def check_entries(
        self,
        knowledge_entries: List[Dict[str, Any]],
        translated_text: str,
        entity_types: Optional[List[EntityType]] = None,
    ) -> None:
        allowed = frozenset(entity_types) if entity_types else REPORTABLE_TYPES

        for entry in knowledge_entries:
            entity_type_raw = str(entry.get("entity_type", ""))
            try:
                etype = EntityType(entity_type_raw)
            except ValueError:
                continue

            if etype not in allowed:
                continue

            expected = str(entry.get("canonical", ""))
            if not expected:
                continue

            source = str(entry.get("source", ""))

            self.check_one(
                source=source,
                expected=expected,
                translated_text=translated_text,
                entity_type=etype,
                knowledge_id=str(entry.get("entity_id", "")),
            )

    # ------------------------------------------------------------------
    # Variant detection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_best_variant(
        expected: str,
        translated_text: str,
        window: int = 50,
    ) -> tuple:
        """Search the translated text for a near-match to *expected*."""
        best_variant = ""
        best_score = 0.0
        best_pos: Optional[int] = None

        start = 0
        while start < len(translated_text):
            chunk = translated_text[start:start + window + len(expected)]
            for i in range(len(chunk) - len(expected) + 1):
                if i < 0:
                    continue
                candidate = chunk[i:i + len(expected)]
                score = _similarity(expected, candidate)
                if score > best_score:
                    best_score = score
                    best_variant = candidate
                    best_pos = start + i
            start += window

        return best_variant, best_score, best_pos

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def matches(self) -> List[EntityMatch]:
        return list(self._matches)

    @property
    def mismatches(self) -> List[EntityMismatch]:
        return list(self._mismatches)

    @property
    def pass_count(self) -> int:
        return len(self._matches)

    @property
    def mismatch_count(self) -> int:
        return len(self._mismatches)

    def summary(self) -> Dict[str, int]:
        return {
            "match": self.pass_count,
            "mismatch": self.mismatch_count,
            "total": self.pass_count + self.mismatch_count,
        }


# -- convenience factories -----------------------------------------------

def match_entity(source: str, expected: str, found: str, entity_type: EntityType, position: Optional[int] = None) -> EntityMatch:
    return EntityMatch(source=source, expected=expected, found=found, entity_type=entity_type, position=position)


def miss_entity(source: str, expected: str, found: str, entity_type: EntityType, severity: Severity = Severity.HIGH) -> EntityMismatch:
    return EntityMismatch(source=source, expected=expected, found=found, entity_type=entity_type, severity=severity)
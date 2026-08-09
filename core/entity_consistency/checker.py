"""RM-7.1 Consistency Checker — compare scanner results against expected forms.

- For every knowledge entry the checker verifies that the canonical
  target form appears in the translation (or identifies a mismatch).
- Fuzzy detection: if the canonical form is missing but a close variant
  is found, a mismatch is reported with severity based on edit distance.
- Unicode variant normalization: CJK Compatibility Ideographs and other
  Traditional Chinese variants are normalized for comparison ONLY.
  Original translation output and knowledge entries are never mutated.
- RM-7.3.2 P3b: Form-Aware Matching Policy for FULL/GIVEN/FAMILY/FORMAL/INTIMATE.
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
from core.entity_consistency.variants import find_normalized
from core.entity_consistency.matching_policy import (
    FormAwareMatchingPolicy,
    MatchResult,
    NameFormType,
    create_matching_policy,
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
        self._form_policy: Optional[FormAwareMatchingPolicy] = None

    def clear(self) -> None:
        self._matches.clear()
        self._mismatches.clear()
        self._form_policy = None

    def set_form_policy(self, policy: FormAwareMatchingPolicy) -> None:
        """Set the form-aware matching policy for form-specific checks."""
        self._form_policy = policy

    def _get_form_type_from_source(self, source: str, entity_type: EntityType) -> Optional[NameFormType]:
        """Infer the name form type from the source text and entity type."""
        if entity_type != EntityType.CHARACTER:
            return None

        # Check for FORMAL suffixes (Chinese + Korean)
        formal_suffixes = ["先生", "氏", "様", "さん", "씨", "님", "선생"]
        for suffix in formal_suffixes:
            if source.endswith(suffix):
                return NameFormType.FORMAL

        # Check for INTIMATE suffixes (Chinese + Korean)
        intimate_suffixes = ["啊", "呀", "啦", "喔", "耶", "야", "아", "이"]
        for suffix in intimate_suffixes:
            if source.endswith(suffix):
                return NameFormType.INTIMATE

        # Single character -> likely FAMILY_NAME
        if len(source) == 1:
            return NameFormType.FAMILY_NAME

        # Two characters -> likely GIVEN_NAME (for Korean names)
        if len(source) == 2:
            return NameFormType.GIVEN_NAME

        # Three+ characters -> likely FULL_NAME
        return NameFormType.FULL_NAME

    # ------------------------------------------------------------------
    # Core check (legacy - simple canonical match)
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

        # Variant-aware exact match: normalize both sides for comparison only
        pos = find_normalized(translated_text, expected)
        if pos != -1:
            # Extract the actual text found at this position (preserves original variant)
            found_text = translated_text[pos:pos + len(expected)]
            match = EntityMatch(
                source=source,
                expected=expected,
                found=found_text,
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

    # ------------------------------------------------------------------
    # Form-Aware check (RM-7.3.2 P3b)
    # ------------------------------------------------------------------

    def check_one_form_aware(
        self,
        source: str,
        expected: str,
        translated_text: str,
        entity_type: EntityType,
        knowledge_id: Optional[str] = None,
    ) -> Optional[EntityMismatch]:
        """Form-aware check using the matching policy.

        This method uses the FormAwareMatchingPolicy to validate that
        the correct surface form appears in the translation, with proper
        handling of FORMAL (supports both family+honorific and full+honorific)
        and INTIMATE (only given+suffix, never full+suffix).
        """
        if not self._form_policy:
            # Fall back to legacy check
            return self.check_one(source, expected, translated_text, entity_type, knowledge_id)

        # Infer form type from source
        form_type = self._get_form_type_from_source(source, entity_type)
        if not form_type:
            # Not a character form type, use legacy check
            return self.check_one(source, expected, translated_text, entity_type, knowledge_id)

        # Use matching policy
        result = self._form_policy.check_match(form_type, translated_text)

        if result == MatchResult.MATCH:
            # Find position for match record
            pos = self._form_policy.find_match_position(form_type, translated_text)
            if pos is not None:
                # Get the actual text found (preserves variant)
                spec = self._form_policy.get_spec(form_type)
                if spec and spec.allowed_patterns:
                    for allowed in spec.allowed_patterns:
                        norm_allowed = self._normalize_for_policy(allowed)
                        norm_text = self._normalize_for_policy(translated_text)
                        if norm_allowed in norm_text:
                            idx = norm_text.find(norm_allowed)
                            found_text = translated_text[idx:idx + len(allowed)]
                            match = EntityMatch(
                                source=source,
                                expected=expected,
                                found=found_text,
                                entity_type=entity_type,
                                position=idx,
                            )
                            self._matches.append(match)
                            return None

            # Fallback: record match with expected
            match = EntityMatch(
                source=source,
                expected=expected,
                found=expected,
                entity_type=entity_type,
                position=pos or 0,
            )
            self._matches.append(match)
            return None

        if result == MatchResult.MISMATCH:
            # Find what was actually found for reporting
            spec = self._form_policy.get_spec(form_type)
            found_text = ""
            if spec and spec.forbidden_patterns:
                norm_text = self._normalize_for_policy(translated_text)
                for forbidden in spec.forbidden_patterns:
                    norm_forbidden = self._normalize_for_policy(forbidden)
                    if norm_forbidden in norm_text:
                        idx = norm_text.find(norm_forbidden)
                        found_text = translated_text[idx:idx + len(forbidden)]
                        break

            mismatch = EntityMismatch(
                source=source,
                expected=expected,
                found=found_text or f"[FORBIDDEN: {form_type.value}]",
                entity_type=entity_type,
                severity=Severity.HIGH,
                position=-1,
                knowledge_id=knowledge_id,
            )
            self._mismatches.append(mismatch)
            return mismatch

        # NO_EXPECTED_FORM - fall back to legacy
        return self.check_one(source, expected, translated_text, entity_type, knowledge_id)

    def _normalize_for_policy(self, text: str) -> str:
        """Normalize text using variant normalization for policy comparison."""
        from core.entity_consistency.variants import normalize_for_comparison
        return normalize_for_comparison(text)

    def check_entries_form_aware(
        self,
        knowledge_entries: List[Dict[str, Any]],
        translated_text: str,
        entity_types: Optional[List[EntityType]] = None,
    ) -> None:
        """Check entries using form-aware matching policy.

        This is the main entry point for RM-7.3.2 P3b form-aware validation.
        """
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

            self.check_one_form_aware(
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
"""RM-7.3.2 P3b — Entity Form-Aware Matching Policy.

Centralizes matching semantics for FULL / GIVEN / FAMILY / FORMAL / INTIMATE.
Does NOT modify original translations; only normalizes in comparison layer.
Preserves CJK variant normalization from variants.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from core.entity_consistency.variants import normalize_for_comparison, are_variants_equal
from core.entity_normalization.models import NameFormType


class MatchResult(Enum):
    """Result of a form-aware match attempt."""
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NO_EXPECTED_FORM = "NO_EXPECTED_FORM"


@dataclass(frozen=True)
class FormMatchSpec:
    """Specification for how a name form should match in translation.

    Attributes:
        form_type: The canonical name form type.
        allowed_patterns: Patterns that count as a valid match.
        forbidden_patterns: Patterns that explicitly count as mismatch.
        requires_exact: If True, only exact (variant-normalized) match allowed.
        expands_to: Form types this form is allowed to expand to (usually empty).
    """
    form_type: NameFormType
    allowed_patterns: List[str]
    forbidden_patterns: List[str]
    requires_exact: bool = True
    expands_to: List[NameFormType] = None

    def __post_init__(self):
        if self.expands_to is None:
            object.__setattr__(self, 'expands_to', [])


class FormAwareMatchingPolicy:
    """Policy engine for entity form-aware matching.

    This class centralizes all matching semantics for the five primary
    name forms: FULL, GIVEN, FAMILY, FORMAL, INTIMATE.

    Key rules:
    - FORMAL supports both "姓氏＋先生" (family name + honorific) AND "全名＋先生" (full name + honorific)
    - INTIMATE only matches "given_name + intimate_suffix" (e.g., 泰義啊), NOT "full_name + intimate_suffix"
    - GIVEN must NOT match FULL expansion (鄭泰義 when expecting 泰義)
    - FAMILY must NOT match FULL expansion (鄭泰義 when expecting 鄭)
    - CJK variants are normalized in comparison layer only
    - Original translations are never modified
    """

    def __init__(self, entity_forms: Optional[Dict[NameFormType, str]] = None):
        """Initialize with known entity form translations.

        Args:
            entity_forms: Dict mapping NameFormType -> canonical translation.
                         Example: {NameFormType.FULL_NAME: "鄭泰義",
                                   NameFormType.GIVEN_NAME: "泰義",
                                   NameFormType.FAMILY_NAME: "鄭",
                                   NameFormType.FORMAL: "鄭先生",
                                   NameFormType.INTIMATE: "泰義啊"}
        """
        self._entity_forms = entity_forms or {}
        self._specs = self._build_default_specs()

    def _build_default_specs(self) -> Dict[NameFormType, FormMatchSpec]:
        """Build default matching specifications for each form type."""
        specs = {}

        # FULL_NAME: exact match only, no expansion allowed
        full = self._entity_forms.get(NameFormType.FULL_NAME, "")
        specs[NameFormType.FULL_NAME] = FormMatchSpec(
            form_type=NameFormType.FULL_NAME,
            allowed_patterns=[full] if full else [],
            forbidden_patterns=[],
            requires_exact=True,
            expands_to=[],
        )

        # GIVEN_NAME: exact match only; must NOT match FULL_NAME expansion
        given = self._entity_forms.get(NameFormType.GIVEN_NAME, "")
        full = self._entity_forms.get(NameFormType.FULL_NAME, "")
        specs[NameFormType.GIVEN_NAME] = FormMatchSpec(
            form_type=NameFormType.GIVEN_NAME,
            allowed_patterns=[given] if given else [],
            forbidden_patterns=[full] if full else [],  # Must NOT match full name
            requires_exact=True,
            expands_to=[],
        )

        # FAMILY_NAME: exact match only; must NOT match FULL_NAME expansion
        family = self._entity_forms.get(NameFormType.FAMILY_NAME, "")
        full = self._entity_forms.get(NameFormType.FULL_NAME, "")
        specs[NameFormType.FAMILY_NAME] = FormMatchSpec(
            form_type=NameFormType.FAMILY_NAME,
            allowed_patterns=[family] if family else [],
            forbidden_patterns=[full] if full else [],  # Must NOT match full name
            requires_exact=True,
            expands_to=[],
        )

        # FORMAL: supports TWO patterns:
        #   1. family_name + honorific (e.g., 鄭先生)
        #   2. full_name + honorific (e.g., 鄭泰義先生)
        formal = self._entity_forms.get(NameFormType.FORMAL, "")
        family = self._entity_forms.get(NameFormType.FAMILY_NAME, "")
        full = self._entity_forms.get(NameFormType.FULL_NAME, "")
        allowed = []
        if formal:
            allowed.append(formal)
        # Also allow the two formal patterns if we can derive them
        if family:
            allowed.append(family + "先生")
        if full:
            allowed.append(full + "先生")
        # Deduplicate
        allowed = list(dict.fromkeys(allowed))
        specs[NameFormType.FORMAL] = FormMatchSpec(
            form_type=NameFormType.FORMAL,
            allowed_patterns=allowed,
            forbidden_patterns=[],
            requires_exact=True,
            expands_to=[],
        )

        # INTIMATE: ONLY matches given_name + intimate_suffix
        # MUST NOT match full_name + intimate_suffix (e.g., 鄭泰義啊 is WRONG)
        intimate = self._entity_forms.get(NameFormType.INTIMATE, "")
        given = self._entity_forms.get(NameFormType.GIVEN_NAME, "")
        full = self._entity_forms.get(NameFormType.FULL_NAME, "")
        allowed = []
        if intimate:
            allowed.append(intimate)
        if given:
            allowed.append(given + "啊")
        forbidden = []
        if full:
            forbidden.append(full + "啊")  # 鄭泰義啊 is FORBIDDEN for INTIMATE
        specs[NameFormType.INTIMATE] = FormMatchSpec(
            form_type=NameFormType.INTIMATE,
            allowed_patterns=allowed,
            forbidden_patterns=forbidden,
            requires_exact=True,
            expands_to=[],
        )

        return specs

    def update_entity_forms(self, entity_forms: Dict[NameFormType, str]) -> None:
        """Update the known entity forms and rebuild specs."""
        self._entity_forms = entity_forms
        self._specs = self._build_default_specs()

    def get_spec(self, form_type: NameFormType) -> Optional[FormMatchSpec]:
        """Get the matching spec for a form type."""
        return self._specs.get(form_type)

    def _find_standalone_occurrences(self, norm_text: str, pattern: str, form_type: NameFormType) -> List[int]:
        """Find positions where pattern appears as a standalone form (not part of a longer form).

        For GIVEN_NAME: pattern should NOT be immediately preceded by family_name
        For FAMILY_NAME: pattern should NOT be immediately followed by given_name
        For INTIMATE: pattern should NOT be immediately preceded by full_name (without intimate suffix)
        For FULL_NAME/FORMAL: no special boundary checks needed
        """
        positions = []
        start = 0
        pattern_len = len(pattern)

        # Get context forms for boundary checking
        family_name = self._entity_forms.get(NameFormType.FAMILY_NAME, "")
        given_name = self._entity_forms.get(NameFormType.GIVEN_NAME, "")
        full_name = self._entity_forms.get(NameFormType.FULL_NAME, "")

        norm_family = normalize_for_comparison(family_name) if family_name else ""
        norm_given = normalize_for_comparison(given_name) if given_name else ""
        norm_full = normalize_for_comparison(full_name) if full_name else ""

        while True:
            pos = norm_text.find(pattern, start)
            if pos == -1:
                break

            # Check boundary conditions based on form type
            is_standalone = True

            if form_type == NameFormType.GIVEN_NAME and norm_family:
                # Given name should NOT be immediately preceded by family name
                # e.g., "泰義" in "鄭泰義" is NOT standalone (preceded by "鄭")
                if pos >= len(norm_family) and norm_text[pos - len(norm_family):pos] == norm_family:
                    is_standalone = False

            elif form_type == NameFormType.FAMILY_NAME and norm_given:
                # Family name should NOT be immediately followed by given name
                # e.g., "鄭" in "鄭泰義" is NOT standalone (followed by "泰義")
                end_pos = pos + pattern_len
                if end_pos + len(norm_given) <= len(norm_text) and norm_text[end_pos:end_pos + len(norm_given)] == norm_given:
                    is_standalone = False

            elif form_type == NameFormType.INTIMATE and norm_full:
                # Intimate should NOT be immediately preceded by full name (without suffix)
                # e.g., "泰義啊" in "鄭泰義啊" is NOT standalone (preceded by "鄭")
                # The intimate pattern is typically given_name + suffix, so we check if
                # it's preceded by the family name part
                if pos >= len(norm_family) and norm_text[pos - len(norm_family):pos] == norm_family:
                    is_standalone = False

            if is_standalone:
                positions.append(pos)

            start = pos + 1

        return positions

    def check_match(
        self,
        form_type: NameFormType,
        translated_text: str,
        position: Optional[int] = None
    ) -> MatchResult:
        """Check if a form type matches in the translated text.

        Args:
            form_type: The form type to check.
            translated_text: The translation text to search in.
            position: Optional position hint (not used, kept for interface compatibility).

        Returns:
            MatchResult.MATCH if the allowed form is present as a standalone occurrence.
            MatchResult.MISMATCH if forbidden pattern found WITHOUT allowed pattern
                              (expansion detected), or if neither found.
            MatchResult.NO_EXPECTED_FORM if no expected form is defined.
        """
        spec = self._specs.get(form_type)
        if not spec or not spec.allowed_patterns:
            return MatchResult.NO_EXPECTED_FORM

        norm_text = normalize_for_comparison(translated_text)

        # Check allowed patterns for standalone occurrences
        allowed_found = False
        for allowed in spec.allowed_patterns:
            norm_allowed = normalize_for_comparison(allowed)
            positions = self._find_standalone_occurrences(norm_text, norm_allowed, form_type)
            if positions:
                allowed_found = True
                break

        if allowed_found:
            return MatchResult.MATCH

        # Allowed pattern not found as standalone - check if forbidden pattern exists (expansion)
        for forbidden in spec.forbidden_patterns:
            norm_forbidden = normalize_for_comparison(forbidden)
            if norm_forbidden in norm_text:
                return MatchResult.MISMATCH

        # Neither allowed nor forbidden found
        return MatchResult.MISMATCH

    def find_match_position(
        self,
        form_type: NameFormType,
        translated_text: str
    ) -> Optional[int]:
        """Find the position of a matching form in translated text.

        Returns the character offset of the first STANDALONE match, or None if not found.
        """
        spec = self._specs.get(form_type)
        if not spec or not spec.allowed_patterns:
            return None

        norm_text = normalize_for_comparison(translated_text)

        for allowed in spec.allowed_patterns:
            norm_allowed = normalize_for_comparison(allowed)
            positions = self._find_standalone_occurrences(norm_text, norm_allowed, form_type)
            if positions:
                return positions[0]

        return None

    def get_all_specs(self) -> Dict[NameFormType, FormMatchSpec]:
        """Get all matching specs (read-only)."""
        return dict(self._specs)


def create_matching_policy(
    full_name: str = "",
    given_name: str = "",
    family_name: str = "",
    formal: str = "",
    intimate: str = ""
) -> FormAwareMatchingPolicy:
    """Factory to create a FormAwareMatchingPolicy from individual form translations.

    Args:
        full_name: Canonical full name (e.g., "鄭泰義")
        given_name: Canonical given name (e.g., "泰義")
        family_name: Canonical family name (e.g., "鄭")
        formal: Canonical formal form (e.g., "鄭先生")
        intimate: Canonical intimate form (e.g., "泰義啊")

    Returns:
        Configured FormAwareMatchingPolicy instance.
    """
    entity_forms = {}
    if full_name:
        entity_forms[NameFormType.FULL_NAME] = full_name
    if given_name:
        entity_forms[NameFormType.GIVEN_NAME] = given_name
    if family_name:
        entity_forms[NameFormType.FAMILY_NAME] = family_name
    if formal:
        entity_forms[NameFormType.FORMAL] = formal
    if intimate:
        entity_forms[NameFormType.INTIMATE] = intimate
    return FormAwareMatchingPolicy(entity_forms)


def create_matching_policy_from_entity(entity) -> FormAwareMatchingPolicy:
    """Create a matching policy from a CanonicalEntity.

    Extracts form translations from entity.name_forms.
    """
    entity_forms = {}
    if entity.name_forms.full_name:
        entity_forms[NameFormType.FULL_NAME] = entity.name_forms.full_name.translation
    if entity.name_forms.given_name:
        entity_forms[NameFormType.GIVEN_NAME] = entity.name_forms.given_name.translation
    if entity.name_forms.family_name:
        entity_forms[NameFormType.FAMILY_NAME] = entity.name_forms.family_name.translation
    if entity.name_forms.formal:
        entity_forms[NameFormType.FORMAL] = entity.name_forms.formal.translation
    if entity.name_forms.intimate:
        entity_forms[NameFormType.INTIMATE] = entity.name_forms.intimate.translation
    return FormAwareMatchingPolicy(entity_forms)


__all__ = [
    "MatchResult",
    "FormMatchSpec",
    "FormAwareMatchingPolicy",
    "create_matching_policy",
    "create_matching_policy_from_entity",
]
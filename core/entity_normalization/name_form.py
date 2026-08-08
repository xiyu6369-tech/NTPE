"""RM-7.3 Name Form Classification & Relationship-aware Resolution.

Classifies surface forms and resolves them based on context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CanonicalEntity,
    EntityNameForms,
    EntityType,
    NameFormTranslation,
    NameFormType,
    NormalizationContext,
    NormalizedEntity,
)


# Korean honorific/formality markers
FORMAL_SUFFIXES = ["씨", "님", "선생", "교수", "박사", "과장", "부장", "차장", "팀장", "대표", "사장", "회장"]
INTIMATE_SUFFIXES = ["야", "아", "이", "군", "양", "놈", "년"]
RELATIONSHIP_TERMS = [
    "형", "누나", "오빠", "언니", "동생", "선배", "후배",
    "아버지", "어머니", "아버님", "어머님", "아빠", "엄마",
    "할아버지", "할머니", "할아버님", "할머님",
    "삼촌", "이모", "고모", "숙부", "숙모",
    "사장님", "부장님", "과장님", "팀장님", "선생님",
]


# Pattern for Korean name + suffix
KOREAN_NAME_WITH_SUFFIX = re.compile(r"([가-힣]{2,4})(" + "|".join(FORMAL_SUFFIXES + INTIMATE_SUFFIXES + RELATIONSHIP_TERMS) + r")")


def classify_name_form(
    source_text: str,
    entity: CanonicalEntity,
    context: Optional[NormalizationContext] = None
) -> Tuple[NameFormType, float]:
    """Classify the name form type of a source text.

    Returns:
        (NameFormType, confidence)
    """
    # Direct match with known forms
    for form in entity.name_forms.get_all_forms():
        if form.source == source_text:
            return form.form_type, 1.0

    # Check for formal suffixes
    for suffix in FORMAL_SUFFIXES:
        if source_text.endswith(suffix):
            base = source_text[:-len(suffix)]
            # Check if base matches known name
            if _matches_base(base, entity):
                return NameFormType.FORMAL, 0.9

    # Check for intimate suffixes
    for suffix in INTIMATE_SUFFIXES:
        if source_text.endswith(suffix):
            base = source_text[:-len(suffix)]
            if _matches_base(base, entity):
                return NameFormType.INTIMATE, 0.9

    # Check for relationship terms
    for term in RELATIONSHIP_TERMS:
        if source_text.endswith(term):
            base = source_text[:-len(term)]
            if _matches_base(base, entity):
                return NameFormType.RELATIONSHIP, 0.85

    # Check if it's just the given name (for characters)
    if entity.entity_type == EntityType.CHARACTER:
        given_form = entity.name_forms.given_name
        if given_form and given_form.source == source_text:
            return NameFormType.GIVEN_NAME, 0.95

        family_form = entity.name_forms.family_name
        if family_form and family_form.source == source_text:
            return NameFormType.FAMILY_NAME, 0.9

    # Check nicknames
    for nick in entity.name_forms.nicknames:
        if nick.source == source_text:
            return NameFormType.NICKNAME, 0.9

    # Check titles
    for title in entity.name_forms.titles:
        if title.source == source_text:
            return NameFormType.TITLE, 0.9

    # Default: check if it matches full name with spacing variation
    full_form = entity.name_forms.full_name
    if full_form:
        normalized_source = source_text.replace(" ", "")
        normalized_full = full_form.source.replace(" ", "")
        if normalized_source == normalized_full:
            return NameFormType.FULL_NAME, 0.8

    return NameFormType.FULL_NAME, 0.5  # Default fallback


def _matches_base(base: str, entity: CanonicalEntity) -> bool:
    """Check if base matches any known name form."""
    if not base:
        return False
    for form in entity.name_forms.get_all_forms():
        if form.source == base or form.source.replace(" ", "") == base.replace(" ", ""):
            return True
    return False


def resolve_name_form(
    entity: CanonicalEntity,
    form_type: NameFormType,
    context: Optional[NormalizationContext] = None
) -> Optional[NameFormTranslation]:
    """Get the appropriate translation for a name form type.

    This is the KEY FUNCTION that preserves surface form level.
    """
    # Try exact form match first
    form = entity.name_forms.get_form(form_type)
    if form:
        return form

    # Fallback logic based on form type
    if form_type == NameFormType.FORMAL:
        # Formal: use full name + honorific
        if entity.name_forms.full_name:
            return NameFormTranslation(
                source=entity.name_forms.full_name.source + " 씨",
                translation=entity.name_forms.full_name.translation + "先生",
                form_type=NameFormType.FORMAL,
            )

    elif form_type == NameFormType.INTIMATE:
        # Intimate: use given name + intimate suffix
        if entity.name_forms.given_name:
            return NameFormTranslation(
                source=entity.name_forms.given_name.source + "야",
                translation=entity.name_forms.given_name.translation + "啊",
                form_type=NameFormType.INTIMATE,
            )

    elif form_type == NameFormType.RELATIONSHIP:
        # Relationship: use given name or full name with relationship term
        if entity.name_forms.given_name:
            return NameFormTranslation(
                source=entity.name_forms.given_name.source,
                translation=entity.name_forms.given_name.translation,
                form_type=NameFormType.RELATIONSHIP,
            )

    elif form_type == NameFormType.GIVEN_NAME:
        return entity.name_forms.given_name

    elif form_type == NameFormType.FAMILY_NAME:
        return entity.name_forms.family_name

    # Default to full name
    return entity.name_forms.full_name


def build_normalized_entity(
    source_text: str,
    entity: CanonicalEntity,
    context: Optional[NormalizationContext] = None
) -> Optional[NormalizedEntity]:
    """Build a NormalizedEntity from source text and context.

    This is the main entry point for normalization.
    """
    # Classify the form
    form_type, confidence = classify_name_form(source_text, entity, context)

    # Resolve the appropriate translation
    matched_form = resolve_name_form(entity, form_type, context)
    if not matched_form:
        return None

    return NormalizedEntity(
        source_text=source_text,
        entity_id=entity.entity_id,
        entity_type=entity.entity_type,
        matched_form=matched_form,
        translation=matched_form.translation,
        confidence=confidence,
        context=context,
    )


def extract_context_from_text(
    text: str,
    position: int,
    window: int = 50
) -> NormalizationContext:
    """Extract normalization context from surrounding text."""
    start = max(0, position - window)
    end = min(len(text), position + window)
    surrounding = text[start:end]

    # Simple heuristics for speaker/listener detection
    # Look for dialogue markers
    speaker = None
    listener = None
    relationship_hint = None

    # Check for quotation context
    before = text[max(0, position - 100):position]
    after = text[position:min(len(text), position + 100)]

    # Detect "X said" pattern
    said_match = re.search(r"([가-힣]{2,4})\s*(?:가|이)\s*(?:말했다|말하였다|했다|하였다)", before)
    if said_match:
        speaker = said_match.group(1)

    # Detect "X 아/야" pattern (intimate address)
    intimate_match = re.search(r"([가-힣]{2,4})[아야]", surrounding)
    if intimate_match:
        relationship_hint = "intimate"

    # Detect "X 씨/님" pattern (formal address)
    formal_match = re.search(r"([가-힣]{2,4})\s*(?:씨(?:께|서)?|님(?:께서|서)?)", surrounding)
    if formal_match:
        relationship_hint = "formal"

    return NormalizationContext(
        source_text=text[position:position+10] if position < len(text) else "",
        position=position,
        surrounding_text=surrounding,
        speaker=speaker,
        listener=listener,
        relationship_hint=relationship_hint,
    )


__all__ = [
    "classify_name_form",
    "resolve_name_form",
    "build_normalized_entity",
    "extract_context_from_text",
    "FORMAL_SUFFIXES",
    "INTIMATE_SUFFIXES",
    "RELATIONSHIP_TERMS",
]
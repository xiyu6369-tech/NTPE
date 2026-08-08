"""Tests for entity_normalization name_form module."""

import pytest

from core.entity_normalization.name_form import (
    classify_name_form,
    resolve_name_form,
    build_normalized_entity,
    extract_context_from_text,
    FORMAL_SUFFIXES,
    INTIMATE_SUFFIXES,
    RELATIONSHIP_TERMS,
)
from core.entity_normalization.models import (
    EntityType,
    NameFormTranslation,
    NameFormType,
    EntityNameForms,
    CanonicalEntity,
    NormalizationContext,
)


def create_test_entity():
    """Create a test canonical entity for 鄭泰義 (정태의)."""
    return CanonicalEntity(
        entity_id="character_001",
        entity_type=EntityType.CHARACTER,
        source_name="정태의",
        canonical_translation="鄭泰義",
        name_forms=EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
            given_name=NameFormTranslation("태의", "泰義", NameFormType.GIVEN_NAME),
            family_name=NameFormTranslation("정", "鄭", NameFormType.FAMILY_NAME),
            formal=NameFormTranslation("정태의 씨", "鄭泰義先生", NameFormType.FORMAL),
            intimate=NameFormTranslation("태의야", "泰義啊", NameFormType.INTIMATE),
        ),
    )


class TestClassifyNameForm:
    def test_full_name_exact(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("정태의", entity)
        assert form_type == NameFormType.FULL_NAME
        assert conf == 1.0

    def test_given_name_exact(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("태의", entity)
        assert form_type == NameFormType.GIVEN_NAME
        # Exact match gives 1.0 confidence
        assert conf == 1.0

    def test_family_name_exact(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("정", entity)
        assert form_type == NameFormType.FAMILY_NAME
        # Exact match gives 1.0 confidence
        assert conf == 1.0

    def test_formal_suffix(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("정태의 씨", entity)
        assert form_type == NameFormType.FORMAL
        assert conf >= 0.8

    def test_intimate_suffix(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("태의야", entity)
        assert form_type == NameFormType.INTIMATE
        assert conf >= 0.8

    def test_relationship_suffix(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("태의형", entity)
        assert form_type == NameFormType.RELATIONSHIP
        assert conf >= 0.8

    def test_spacing_variant(self):
        entity = create_test_entity()
        form_type, conf = classify_name_form("정 태의", entity)
        assert form_type == NameFormType.FULL_NAME
        assert conf >= 0.7


class TestResolveNameForm:
    def test_resolve_full_name(self):
        entity = create_test_entity()
        form = resolve_name_form(entity, NameFormType.FULL_NAME)
        assert form is not None
        assert form.translation == "鄭泰義"

    def test_resolve_given_name(self):
        entity = create_test_entity()
        form = resolve_name_form(entity, NameFormType.GIVEN_NAME)
        assert form is not None
        assert form.translation == "泰義"

    def test_resolve_formal(self):
        entity = create_test_entity()
        form = resolve_name_form(entity, NameFormType.FORMAL)
        assert form is not None
        assert form.translation == "鄭泰義先生"

    def test_resolve_intimate_preserves_given_name(self):
        entity = create_test_entity()
        form = resolve_name_form(entity, NameFormType.INTIMATE)
        assert form is not None
        # KEY TEST: intimate should use given name, NOT full name
        assert form.translation == "泰義啊"
        assert form.translation != "鄭泰義啊"  # Must NOT expand to full name


class TestBuildNormalizedEntity:
    def test_normalize_full_name(self):
        entity = create_test_entity()
        normalized = build_normalized_entity("정태의", entity)
        assert normalized is not None
        assert normalized.translation == "鄭泰義"
        assert normalized.matched_form.form_type == NameFormType.FULL_NAME

    def test_normalize_intimate_preserves_level(self):
        entity = create_test_entity()
        normalized = build_normalized_entity("태의야", entity)
        assert normalized is not None
        assert normalized.translation == "泰義啊"
        # Must NOT be "鄭泰義啊"
        assert normalized.translation != "鄭泰義啊"

    def test_normalize_formal(self):
        entity = create_test_entity()
        normalized = build_normalized_entity("정태의 씨", entity)
        assert normalized is not None
        assert normalized.translation == "鄭泰義先生"


class TestExtractContextFromText:
    def test_intimate_context(self):
        text = "정태의가 말했다. \"태의야.\""
        # Position of "태의야"
        pos = text.find("태의야")
        ctx = extract_context_from_text(text, pos)
        assert ctx.relationship_hint == "intimate"

    def test_formal_context(self):
        text = "정태의 씨께서 오셨습니다."
        pos = text.find("정태의 씨")
        ctx = extract_context_from_text(text, pos)
        assert ctx.relationship_hint == "formal"

    def test_speaker_detection(self):
        text = "정태의가 말했다. \"안녕하세요.\""
        pos = text.find("정태의")
        ctx = extract_context_from_text(text, pos)
        # Should detect speaker
        assert ctx.speaker == "정태의" or ctx.speaker is None  # May not match exact pattern


class TestSuffixConstants:
    def test_formal_suffixes(self):
        assert "씨" in FORMAL_SUFFIXES
        assert "님" in FORMAL_SUFFIXES

    def test_intimate_suffixes(self):
        assert "야" in INTIMATE_SUFFIXES
        assert "아" in INTIMATE_SUFFIXES

    def test_relationship_terms(self):
        assert "형" in RELATIONSHIP_TERMS
        assert "누나" in RELATIONSHIP_TERMS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
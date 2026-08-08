"""Tests for entity_normalization models."""

import pytest

from core.entity_normalization.models import (
    EntityType,
    NameFormType,
    ConflictSeverity,
    ResolutionSource,
    NameFormTranslation,
    EntityNameForms,
    CanonicalEntity,
    ConflictRecord,
    NormalizationContext,
    NormalizedEntity,
    NormalizationResult,
)


class TestNameFormTranslation:
    def test_creation(self):
        form = NameFormTranslation(
            source="정태의",
            translation="鄭泰義",
            form_type=NameFormType.FULL_NAME,
        )
        assert form.source == "정태의"
        assert form.translation == "鄭泰義"
        assert form.form_type == NameFormType.FULL_NAME

    def test_to_dict(self):
        form = NameFormTranslation(
            source="태의",
            translation="泰義",
            form_type=NameFormType.GIVEN_NAME,
        )
        d = form.to_dict()
        assert d["source"] == "태의"
        assert d["translation"] == "泰義"
        assert d["form_type"] == "GIVEN_NAME"

    def test_from_dict(self):
        data = {
            "source": "정태의 씨",
            "translation": "鄭泰義先生",
            "form_type": "FORMAL",
            "metadata": {"context": "business"},
        }
        form = NameFormTranslation.from_dict(data)
        assert form.source == "정태의 씨"
        assert form.translation == "鄭泰義先生"
        assert form.form_type == NameFormType.FORMAL


class TestEntityNameForms:
    def test_empty_forms(self):
        forms = EntityNameForms()
        assert forms.full_name is None
        assert forms.given_name is None
        assert forms.get_all_forms() == []

    def test_with_forms(self):
        forms = EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
            given_name=NameFormTranslation("태의", "泰義", NameFormType.GIVEN_NAME),
            family_name=NameFormTranslation("정", "鄭", NameFormType.FAMILY_NAME),
        )
        assert forms.full_name is not None
        assert forms.given_name is not None
        assert forms.family_name is not None

        all_forms = forms.get_all_forms()
        assert len(all_forms) == 3

    def test_get_form(self):
        forms = EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
            intimate=NameFormTranslation("태의야", "泰義啊", NameFormType.INTIMATE),
        )
        assert forms.get_form(NameFormType.FULL_NAME).source == "정태의"
        assert forms.get_form(NameFormType.INTIMATE).source == "태의야"
        assert forms.get_form(NameFormType.GIVEN_NAME) is None

    def test_to_from_dict(self):
        forms = EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
            nicknames=[NameFormTranslation("꼬마", "小鬼", NameFormType.NICKNAME)],
        )
        d = forms.to_dict()
        assert d["full_name"]["source"] == "정태의"
        assert len(d["nicknames"]) == 1

        restored = EntityNameForms.from_dict(d)
        assert restored.full_name.source == "정태의"
        assert len(restored.nicknames) == 1


class TestCanonicalEntity:
    def test_creation(self):
        forms = EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
        )
        entity = CanonicalEntity(
            entity_id="character_001",
            entity_type=EntityType.CHARACTER,
            source_name="정태의",
            canonical_translation="鄭泰義",
            name_forms=forms,
        )
        assert entity.entity_id == "character_001"
        assert entity.entity_type == EntityType.CHARACTER
        assert entity.canonical_translation == "鄭泰義"

    def test_to_from_dict(self):
        forms = EntityNameForms(
            full_name=NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME),
        )
        entity = CanonicalEntity(
            entity_id="character_001",
            entity_type=EntityType.CHARACTER,
            source_name="정태의",
            canonical_translation="鄭泰義",
            name_forms=forms,
            metadata={"novel": "test"},
        )
        d = entity.to_dict()
        assert d["entity_id"] == "character_001"
        assert d["canonical_translation"] == "鄭泰義"

        restored = CanonicalEntity.from_dict(d)
        assert restored.entity_id == "character_001"
        assert restored.metadata["novel"] == "test"


class TestConflictRecord:
    def test_creation(self):
        conflict = ConflictRecord(
            source="정태의",
            entity_type=EntityType.CHARACTER,
            candidates=["鄭泰義", "鄭太義"],
            severity=ConflictSeverity.HIGH,
        )
        assert conflict.source == "정태의"
        assert len(conflict.candidates) == 2
        assert conflict.severity == ConflictSeverity.HIGH
        assert not conflict.is_resolved

    def test_resolved(self):
        conflict = ConflictRecord(
            source="정태의",
            entity_type=EntityType.CHARACTER,
            candidates=["鄭泰義", "鄭太義"],
            resolution="鄭泰義",
            resolution_source=ResolutionSource.USER,
        )
        assert conflict.is_resolved
        assert conflict.resolution == "鄭泰義"
        assert conflict.resolution_source == ResolutionSource.USER


class TestNormalizationContext:
    def test_creation(self):
        ctx = NormalizationContext(
            source_text="태의야",
            position=10,
            surrounding_text="정태의가 말했다. \"태의야.\"",
            relationship_hint="intimate",
        )
        assert ctx.source_text == "태의야"
        assert ctx.position == 10
        assert ctx.relationship_hint == "intimate"


class TestNormalizedEntity:
    def test_creation(self):
        form = NameFormTranslation("태의", "泰義", NameFormType.GIVEN_NAME)
        entity = NormalizedEntity(
            source_text="태의",
            entity_id="character_001",
            entity_type=EntityType.CHARACTER,
            matched_form=form,
            translation="泰義",
            confidence=0.95,
        )
        assert entity.source_text == "태의"
        assert entity.translation == "泰義"
        assert entity.confidence == 0.95


class TestNormalizationResult:
    def test_add_entity(self):
        result = NormalizationResult()
        form = NameFormTranslation("정태의", "鄭泰義", NameFormType.FULL_NAME)
        entity = NormalizedEntity(
            source_text="정태의",
            entity_id="character_001",
            entity_type=EntityType.CHARACTER,
            matched_form=form,
            translation="鄭泰義",
        )
        result = result.add_entity(entity)
        assert len(result.entities) == 1

    def test_add_conflict(self):
        result = NormalizationResult()
        conflict = ConflictRecord(
            source="정태의",
            entity_type=EntityType.CHARACTER,
            candidates=["鄭泰義", "鄭太義"],
        )
        result = result.add_conflict(conflict)
        assert len(result.conflicts) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
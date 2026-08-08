"""Tests for entity_normalization identity module."""

import pytest

from core.entity_normalization.identity import (
    EntityIdentityRegistry,
    build_canonical_entity,
    generate_entity_id,
    map_ke_entity_type,
    get_identity_registry,
    register_entity,
    resolve_entity,
    KE_ENTITY_TYPE_MAP,
    PRIORITY_ORDER,
)
from core.entity_normalization.models import (
    EntityType,
    EntityNameForms,
    NameFormTranslation,
    NameFormType,
)
from core.knowledge_evolution.models import EntityType as KEEntityType, PriorityLevel


class TestGenerateEntityId:
    def test_stable_id(self):
        id1 = generate_entity_id(EntityType.CHARACTER, "정태의")
        id2 = generate_entity_id(EntityType.CHARACTER, "정태의")
        assert id1 == id2
        assert id1.startswith("character_")

    def test_different_types_different_ids(self):
        id1 = generate_entity_id(EntityType.CHARACTER, "정태의")
        id2 = generate_entity_id(EntityType.LOCATION, "정태의")
        assert id1 != id2


class TestMapKEEntityType:
    def test_mapping(self):
        assert map_ke_entity_type(KEEntityType.CHARACTER) == EntityType.CHARACTER
        assert map_ke_entity_type(KEEntityType.LOCATION) == EntityType.LOCATION
        assert map_ke_entity_type(KEEntityType.ORGANIZATION) == EntityType.ORGANIZATION
        assert map_ke_entity_type(KEEntityType.TERM) == EntityType.TERM
        assert map_ke_entity_type(KEEntityType.TITLE) == EntityType.TERM
        assert map_ke_entity_type(KEEntityType.ALIAS) == EntityType.CHARACTER


class TestBuildCanonicalEntity:
    def test_basic_creation(self):
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
        )
        assert entity.entity_type == EntityType.CHARACTER
        assert entity.source_name == "정태의"
        assert entity.canonical_translation == "鄭泰義"
        assert entity.name_forms.full_name is not None
        assert entity.name_forms.full_name.source == "정태의"
        assert entity.name_forms.full_name.translation == "鄭泰義"

    def test_korean_name_inference(self):
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
        )
        # Should infer family and given name (first char = family, rest = given)
        assert entity.name_forms.family_name is not None
        assert entity.name_forms.family_name.source == "정"
        assert entity.name_forms.family_name.translation == "鄭"
        assert entity.name_forms.given_name is not None
        assert entity.name_forms.given_name.source == "태의"
        assert entity.name_forms.given_name.translation == "泰義"

    def test_custom_entity_id(self):
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
            entity_id="custom_id_123",
        )
        assert entity.entity_id == "custom_id_123"


class TestEntityIdentityRegistry:
    def test_register_and_get(self):
        registry = EntityIdentityRegistry()
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
        )
        registry.register(entity)

        retrieved = registry.get_by_id(entity.entity_id)
        assert retrieved is not None
        assert retrieved.entity_id == entity.entity_id

    def test_resolve_source(self):
        registry = EntityIdentityRegistry()
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
        )
        registry.register(entity)

        # Direct match
        resolved = registry.resolve_source("정태의")
        assert resolved is not None
        assert resolved.entity_id == entity.entity_id

        # Spacing variant
        resolved = registry.resolve_source("정 태의")
        assert resolved is not None
        assert resolved.entity_id == entity.entity_id

    def test_resolve_by_form(self):
        registry = EntityIdentityRegistry()
        entity = build_canonical_entity(
            source_name="정태의",
            canonical_translation="鄭泰義",
            entity_type=EntityType.CHARACTER,
        )
        registry.register(entity)

        # Resolve by given name
        resolved = registry.resolve_source("태의")
        assert resolved is not None
        assert resolved.entity_id == entity.entity_id

        # Resolve by family name
        resolved = registry.resolve_source("정")
        assert resolved is not None
        assert resolved.entity_id == entity.entity_id

    def test_get_entities_by_type(self):
        registry = EntityIdentityRegistry()
        char_entity = build_canonical_entity("정태의", "鄭泰義", EntityType.CHARACTER)
        loc_entity = build_canonical_entity("서울", "首爾", EntityType.LOCATION)
        registry.register(char_entity)
        registry.register(loc_entity)

        chars = registry.get_entities_by_type(EntityType.CHARACTER)
        assert len(chars) == 1
        assert chars[0].entity_id == char_entity.entity_id

        locs = registry.get_entities_by_type(EntityType.LOCATION)
        assert len(locs) == 1


class TestGlobalRegistry:
    def test_global_functions(self):
        # Clear first
        registry = get_identity_registry()
        registry.clear()

        entity = build_canonical_entity("정태의", "鄭泰義", EntityType.CHARACTER)
        register_entity(entity)

        resolved = resolve_entity("정태의")
        assert resolved is not None
        assert resolved.entity_id == entity.entity_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
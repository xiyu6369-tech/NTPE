"""Tests for Entity Injector (RM-7.2)."""

import pytest

from core.entity_resolver import (
    EntityInjector,
    EntityInjectionSet,
    ResolvedEntity,
    InjectionSource,
    UNKNOWN_TRANSLATION,
    ENTITY_MAPPING_SECTION_NAME,
    ENTITY_MAPPING_VERSION,
)
from core.prompt_runtime.models import PromptSection


def test_injector_basic():
    """Test basic entity injection."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", entity_type="CHARACTER", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="일레이", target="伊萊", entity_type="CHARACTER", source_level=InjectionSource.RUNTIME.value),
        ResolvedEntity(source="서울", target="Seoul", entity_type="PLACE", source_level=InjectionSource.RUNTIME.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert section.name == ENTITY_MAPPING_SECTION_NAME
    assert section.version == ENTITY_MAPPING_VERSION
    assert "정태的" in section.content
    assert "鄭泰義" in section.content
    assert "일레이" in section.content
    assert "伊萊" in section.content
    assert "서울" in section.content
    assert "Seoul" in section.content
    assert section.metadata["entity_count"] == 3
    assert section.metadata["known_count"] == 3
    assert section.metadata["unknown_count"] == 0


def test_injector_with_unknown():
    """Test injection with unknown entities."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="모르는사람", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(include_unknown=True)
    section = injector.inject(injection_set)

    assert "모르는사람" in section.content
    assert UNKNOWN_TRANSLATION in section.content
    assert section.metadata["unknown_count"] == 1


def test_injector_without_unknown():
    """Test injection excluding unknown entities."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="모르는사람", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(include_unknown=False)
    section = injector.inject(injection_set)

    assert "정태的" in section.content
    assert "모르는사람" not in section.content
    assert section.metadata["known_count"] == 1
    assert section.metadata["unknown_count"] == 1


def test_injector_user_override_marker():
    """Test that USER OVERRIDE entities are marked."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="일레이", target="伊萊", source_level=InjectionSource.RUNTIME.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert "[USER OVERRIDE]" in section.content
    # USER OVERRIDE marker should be on 정태的 line
    lines = section.content.split("\n")
    for line in lines:
        if "정태的" in line:
            assert "[USER OVERRIDE]" in line


def test_injector_group_by_type():
    """Test grouping entities by type."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", entity_type="CHARACTER", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="일레이", target="伊萊", entity_type="CHARACTER", source_level=InjectionSource.RUNTIME.value),
        ResolvedEntity(source="서울", target="Seoul", entity_type="PLACE", source_level=InjectionSource.RUNTIME.value),
        ResolvedEntity(source="용어", target="Term", entity_type="TERMINOLOGY", source_level=InjectionSource.RUNTIME.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(group_by_type=True)
    section = injector.inject(injection_set)

    assert "## CHARACTER" in section.content
    assert "## PLACE" in section.content
    assert "## TERMINOLOGY" in section.content
    # Order should be CHARACTER, PLACE, ORGANIZATION, TERMINOLOGY, UNKNOWN
    char_pos = section.content.index("## CHARACTER")
    place_pos = section.content.index("## PLACE")
    term_pos = section.content.index("## TERMINOLOGY")
    assert char_pos < place_pos < term_pos


def test_injector_no_grouping():
    """Test flat list without grouping."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", entity_type="CHARACTER", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="서울", target="Seoul", entity_type="PLACE", source_level=InjectionSource.RUNTIME.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(group_by_type=False)
    section = injector.inject(injection_set)

    assert "## CHARACTER" not in section.content
    assert "## PLACE" not in section.content
    # Should be flat list
    lines = [l for l in section.content.split("\n") if l.strip()]
    assert len(lines) == 2


def test_injector_empty_set():
    """Test injection with empty entity set."""
    injection_set = EntityInjectionSet(entities=[])

    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert "No entities found" in section.content
    assert section.metadata["entity_count"] == 0


def test_injector_minimal():
    """Test minimal injection mode."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="모르는사람", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector()
    section = injector.inject_minimal(injection_set)

    # Only known entities
    assert "정태的" in section.content
    assert "鄭泰義" in section.content
    assert "모르는사람" not in section.content
    assert "[USER OVERRIDE]" not in section.content
    assert section.metadata["mode"] == "minimal"


def test_injector_returns_prompt_section():
    """Test that injector returns PromptSection."""
    entities = [ResolvedEntity(source="정태的", target="鄭泰義")]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert isinstance(section, PromptSection)
    assert section.name == ENTITY_MAPPING_SECTION_NAME


def test_build_entity_mapping_section():
    """Test convenience function."""
    from core.entity_resolver import build_entity_mapping_section

    entities = [ResolvedEntity(source="정태的", target="鄭泰義")]
    injection_set = EntityInjectionSet(entities=entities)

    section = build_entity_mapping_section(injection_set, include_unknown=True)

    assert isinstance(section, PromptSection)
    assert section.name == ENTITY_MAPPING_SECTION_NAME
    assert "정태的" in section.content


def test_injector_unknown_marker():
    """Test custom unknown marker."""
    entities = [
        ResolvedEntity(source="모름", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(unknown_marker="(번역 없음)")
    section = injector.inject(injection_set)

    assert "(번역 없음)" in section.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
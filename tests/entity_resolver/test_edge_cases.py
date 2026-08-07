"""Edge case tests for Entity Resolver (RM-7.2)."""

import pytest

from core.entity_resolver import (
    EntityExtractor,
    EntityResolver,
    EntityInjector,
    EntityInjectionSet,
    ResolvedEntity,
    ExtractedEntity,
    EntityType,
    InjectionSource,
    UNKNOWN_TRANSLATION,
    build_known_entities_from_runtime,
)
from core.knowledge_runtime.merger import MergedRuntime, MergedKnowledge


class MockRuntime:
    """Mock MergedRuntime for testing."""

    def __init__(self, domains: dict):
        self.domains = {}
        for name, entries in domains.items():
            self.domains[name] = MergedKnowledge(
                domain=name,
                entries=entries,
                strategy="key_override",
            )

    def get_domain(self, domain: str):
        return self.domains.get(domain)


def test_empty_entity_list():
    """Test handling of completely empty entity list."""
    injection_set = EntityInjectionSet(entities=[])

    assert injection_set.count == 0
    assert injection_set.get_known_entities() == []
    assert injection_set.get_unknown_entities() == []
    assert injection_set.get_by_source("anything") is None

    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert section.metadata["entity_count"] == 0
    assert section.metadata["known_count"] == 0
    assert section.metadata["unknown_count"] == 0
    assert "No entities found" in section.content


def test_resolver_with_empty_extracted():
    """Test resolver with empty extracted list."""
    runtime = MockRuntime({"character": {"정태的": "鄭泰義"}})
    resolver = EntityResolver(runtime=runtime)

    result = resolver.resolve([])

    assert result.count == 0
    assert result.metadata["total_extracted"] == 0
    assert all(v == 0 for v in [
        result.metadata["user_overrides"],
        result.metadata["runtime_resolved"],
        result.metadata["learning_resolved"],
        result.metadata["auto_unknown"],
    ])


def test_extractor_with_empty_known_entities():
    """Test extractor with no known entities configured."""
    extractor = EntityExtractor(known_entities={})

    chunk = "정태的가 왔다."
    extracted = extractor.extract(chunk)

    # Should not extract anything without known entities
    assert extracted == []


def test_entity_with_empty_target():
    """Test ResolvedEntity with empty target string."""
    entity = ResolvedEntity(source="테스트", target="")

    assert entity.is_known is False  # Empty target means not known
    assert entity.target == ""


def test_entity_with_whitespace_target():
    """Test ResolvedEntity with whitespace-only target."""
    entity = ResolvedEntity(source="테스트", target="   ")

    assert entity.is_known is True  # Whitespace is still a target


def test_unknown_translation_constant():
    """Test UNKNOWN_TRANSLATION constant value."""
    assert UNKNOWN_TRANSLATION == "(No predefined translation)"

    entity = ResolvedEntity(
        source="모름",
        target=UNKNOWN_TRANSLATION,
        source_level=InjectionSource.AUTO.value,
    )

    assert entity.is_known is False
    assert entity.target == UNKNOWN_TRANSLATION


def test_injector_with_only_unknown_entities():
    """Test injector when all entities are unknown."""
    entities = [
        ResolvedEntity(source="모름1", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
        ResolvedEntity(source="모름2", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(include_unknown=True)
    section = injector.inject(injection_set)

    assert section.metadata["known_count"] == 0
    assert section.metadata["unknown_count"] == 2
    assert "모름1" in section.content
    assert "모름2" in section.content
    assert UNKNOWN_TRANSLATION in section.content


def test_injector_exclude_unknown_when_all_unknown():
    """Test injector excluding unknown when all are unknown."""
    entities = [
        ResolvedEntity(source="모름", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    injector = EntityInjector(include_unknown=False)
    section = injector.inject(injection_set)

    assert "No predefined entity translations" in section.content
    assert section.metadata["known_count"] == 0


def test_resolver_empty_runtime():
    """Test resolver with completely empty runtime."""
    runtime = MockRuntime({})
    resolver = EntityResolver(runtime=runtime)

    extracted = [ExtractedEntity(source="테스트", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    assert result.count == 1
    assert result.entities[0].source_level == InjectionSource.AUTO.value
    assert result.entities[0].target == UNKNOWN_TRANSLATION


def test_resolver_none_runtime():
    """Test resolver with None runtime."""
    resolver = EntityResolver(runtime=None)

    extracted = [ExtractedEntity(source="테스트", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    assert result.count == 1
    assert result.entities[0].source_level == InjectionSource.AUTO.value


def test_user_override_with_empty_string():
    """Test USER override with empty target (should still win)."""
    runtime = MockRuntime({"character": {"정태的": "鄭泰義_RUNTIME"}})
    user_overrides = {"정태的": ""}  # Empty override

    resolver = EntityResolver(runtime=runtime, user_overrides=user_overrides)

    extracted = [ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    # USER override should still win even if empty
    assert result.entities[0].source_level == InjectionSource.USER.value
    assert result.entities[0].target == ""
    assert result.entities[0].is_user_override is True


def test_multiple_occurrences_same_entity():
    """Test multiple occurrences of same entity in chunk."""
    known = {"정태的": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    chunk = "정태的가 정태的를 불렀다. 정태的가 대답했다."
    extracted = extractor.extract(chunk)

    # Should only extract once (deduplicated)
    assert len(extracted) == 1
    assert extracted[0].source == "정태的"


def test_entity_at_chunk_boundaries():
    """Test entity at beginning and end of chunk."""
    known = {"시작": EntityType.CHARACTER.value, "끝": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    chunk = "시작 중간에 끝"
    extracted = extractor.extract(chunk)

    assert len(extracted) == 2
    assert extracted[0].source == "시작"
    assert extracted[0].position == 0
    assert extracted[1].source == "끝"
    assert extracted[1].position > extracted[0].position


def test_entity_with_special_characters():
    """Test entity names with special characters."""
    known = {"정태的·김": EntityType.CHARACTER.value, "A-팀": EntityType.ORGANIZATION.value}
    extractor = EntityExtractor(known_entities=known)

    chunk = "정태的·김과 A-팀이 만났다."
    extracted = extractor.extract(chunk)

    assert len(extracted) == 2
    sources = {e.source for e in extracted}
    assert "정태的·김" in sources
    assert "A-팀" in sources


def test_case_sensitivity():
    """Test that entity matching is case-sensitive for Korean (which doesn't have case)."""
    known = {"정태的": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    # Korean doesn't have case, but test exact match
    chunk = "정태的"
    extracted = extractor.extract(chunk)
    assert len(extracted) == 1


def test_very_long_chunk():
    """Test extraction from very long chunk."""
    known = {"정태的": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    # Create a long chunk with entity in middle
    chunk = "가" * 1000 + "정태的" + "나" * 1000
    extracted = extractor.extract(chunk)

    assert len(extracted) == 1
    assert extracted[0].source == "정태的"
    assert extracted[0].position == 1000


def test_many_entities_in_chunk():
    """Test chunk with many entities."""
    known = {f"이름{i}": EntityType.CHARACTER.value for i in range(50)}
    extractor = EntityExtractor(known_entities=known)

    chunk = " ".join(f"이름{i}" for i in range(50))
    extracted = extractor.extract(chunk)

    assert len(extracted) == 50


def test_resolver_metadata_accuracy():
    """Test that resolver metadata accurately reflects resolution."""
    runtime = MockRuntime({"character": {"정태的": "鄭泰義"}})
    user_overrides = {"사용자": "USER"}
    learning = {"학습": "LEARNING"}

    resolver = EntityResolver(
        runtime=runtime,
        user_overrides=user_overrides,
        learning_data=learning,
    )

    extracted = [
        ExtractedEntity(source="사용자", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="학습", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="모름", entity_type=EntityType.UNKNOWN.value),
    ]
    result = resolver.resolve(extracted)

    # Verify exact counts
    assert result.metadata["user_overrides"] == 1
    assert result.metadata["runtime_resolved"] == 1
    assert result.metadata["learning_resolved"] == 1
    assert result.metadata["auto_unknown"] == 1
    assert result.metadata["total_extracted"] == 4


def test_entity_type_preservation():
    """Test that entity types are preserved through pipeline."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義"},
        "scene": {"서울": "Seoul"},
        "glossary": {"용어": "Term"},
    })

    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "정태的가 서울에서 용어를 사용했다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(runtime=runtime)
    injection_set = resolver.resolve(extracted)

    # Check entity types preserved
    types = {e.source: e.entity_type for e in injection_set.entities}
    assert types["정태的"] == EntityType.CHARACTER.value
    assert types["서울"] == EntityType.PLACE.value
    assert types["용어"] == EntityType.TERMINOLOGY.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Integration tests for Entity Resolver pipeline (RM-7.2)."""

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
from core.prompt_runtime.models import PromptSection


class MockRuntime:
    """Mock MergedRuntime for testing."""

    def __init__(self, domains: dict):
        self.domains = {}
        self.version = "rm-6.1.2"  # Add version for PromptBuilder
        for name, entries in domains.items():
            self.domains[name] = MergedKnowledge(
                domain=name,
                entries=entries,
                strategy="key_override",
            )

    def get_domain(self, domain: str):
        return self.domains.get(domain)


def test_full_pipeline_user_override():
    """Test full pipeline: extract -> resolve -> inject with USER override."""
    # Setup runtime with character data
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義_RUNTIME", "일레이": "伊萊"},
    })

    # User overrides 정태的
    user_overrides = {"정태的": "鄭泰義_USER"}

    # 1. Extract
    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "정태的가 일레이를 만났다."
    extracted = extractor.extract(chunk)

    assert len(extracted) == 2

    # 2. Resolve
    resolver = EntityResolver(runtime=runtime, user_overrides=user_overrides)
    injection_set = resolver.resolve(extracted)

    assert injection_set.count == 2
    # USER override should win for 정태的
    정태的_entity = injection_set.get_by_source("정태的")
    assert 정태的_entity.target == "鄭泰義_USER"
    assert 정태的_entity.is_user_override is True

    # 3. Inject
    injector = EntityInjector()
    section = injector.inject(injection_set)

    assert "정태的 → 鄭泰義_USER [USER OVERRIDE]" in section.content
    assert "일레이 → 伊萊" in section.content


def test_full_pipeline_runtime_fallback():
    """Test full pipeline with RUNTIME fallback (no USER override)."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義", "일레이": "伊萊"},
        "scene": {"서울": "Seoul"},
    })

    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "정태的가 서울에서 일레이를 만났다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(runtime=runtime)  # No user overrides
    injection_set = resolver.resolve(extracted)

    # All should come from RUNTIME
    assert injection_set.metadata["runtime_resolved"] == 3
    assert injection_set.metadata["user_overrides"] == 0

    for entity in injection_set.entities:
        assert entity.source_level == InjectionSource.RUNTIME.value
        assert entity.is_known is True


def test_full_pipeline_learning_fallback():
    """Test full pipeline with LEARNING fallback."""
    runtime = MockRuntime({})  # Empty runtime

    # Learning data from historical translations
    learning = {
        "크리스토프": "克里斯托夫",
        "에드워드": "愛德華",
    }

    known_entities = build_known_entities_from_runtime(runtime)
    # Add learning entities to known_entities for extraction
    known_entities.update({k: EntityType.CHARACTER.value for k in learning})

    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "크리스토프와 에드워드가 대화했다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(runtime=runtime, learning_data=learning)
    injection_set = resolver.resolve(extracted)

    # Should come from LEARNING
    assert injection_set.metadata["learning_resolved"] == 2

    for entity in injection_set.entities:
        assert entity.source_level == InjectionSource.LEARNING.value
        assert entity.metadata.get("source") == "learning"


def test_full_pipeline_unknown_entities():
    """Test full pipeline with completely unknown entities."""
    runtime = MockRuntime({})

    known_entities = build_known_entities_from_runtime(runtime)
    # Add unknown entity to known_entities for extraction (simulating pattern match)
    known_entities["완전히모르는이름"] = EntityType.UNKNOWN.value

    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "완전히모르는이름이 나타났다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(runtime=runtime)
    injection_set = resolver.resolve(extracted)

    # Should be AUTO/UNKNOWN
    assert injection_set.metadata["auto_unknown"] == 1

    entity = injection_set.entities[0]
    assert entity.target == UNKNOWN_TRANSLATION
    assert entity.source_level == InjectionSource.AUTO.value
    assert entity.is_known is False


def test_full_pipeline_mixed_sources():
    """Test pipeline with mixed resolution sources."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義_RUNTIME"},
        "glossary": {"신림동": "Sillim-dong"},
    })
    user_overrides = {"정태的": "鄭泰義_USER"}
    learning = {"크리스토프": "克里斯托夫"}

    # Add learning entities for extraction
    known_entities = build_known_entities_from_runtime(runtime)
    known_entities["크리스토프"] = EntityType.CHARACTER.value

    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "정태的와 크리스토프가 신림동에서 만났다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(
        runtime=runtime,
        user_overrides=user_overrides,
        learning_data=learning,
    )
    injection_set = resolver.resolve(extracted)

    # Check each entity has correct source
    sources = {e.source: e.source_level for e in injection_set.entities}
    assert sources["정태的"] == InjectionSource.USER.value
    assert sources["크리스토프"] == InjectionSource.LEARNING.value
    assert sources["신림동"] == InjectionSource.RUNTIME.value


def test_empty_chunk_pipeline():
    """Test pipeline with empty chunk."""
    runtime = MockRuntime({"character": {"정태的": "鄭泰義"}})
    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    extracted = extractor.extract("")
    assert extracted == []

    resolver = EntityResolver(runtime=runtime)
    injection_set = resolver.resolve(extracted)
    assert injection_set.count == 0

    injector = EntityInjector()
    section = injector.inject(injection_set)
    assert "No entities found" in section.content


def test_chunk_with_no_known_entities():
    """Test chunk that has no known entities."""
    runtime = MockRuntime({"character": {"정태的": "鄭泰義"}})
    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "아무도 모르는 이야기다."
    extracted = extractor.extract(chunk)
    assert extracted == []


def test_prompt_section_integration():
    """Test that injected section integrates with PromptAssembly."""
    from core.prompt_runtime.builder import build_prompt

    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義"},
    })
    user_overrides = {"정태的": "鄭泰義_USER"}

    known_entities = build_known_entities_from_runtime(runtime)
    extractor = EntityExtractor(known_entities=known_entities)

    chunk = "정태的가 왔다."
    extracted = extractor.extract(chunk)

    resolver = EntityResolver(runtime=runtime, user_overrides=user_overrides)
    injection_set = resolver.resolve(extracted)

    # Build prompt with entity mapping
    assembly = build_prompt(runtime, chunk_text=chunk, entity_injection_set=injection_set)

    # Verify section order
    section_names = [s.name for s in assembly.sections]
    assert section_names == [
        "System",
        "Character",
        "Entity Mapping",
        "Glossary",
        "Scene",
        "Narrative",
        "Style",
        "Chunk",
    ]

    # Find Entity Mapping section
    entity_section = next(s for s in assembly.sections if s.name == "Entity Mapping")
    assert "정태的 → 鄭泰義_USER [USER OVERRIDE]" in entity_section.content


def test_injection_set_serialization():
    """Test EntityInjectionSet serialization."""
    entities = [
        ResolvedEntity(
            source="정태的",
            target="鄭泰義",
            entity_type="CHARACTER",
            source_level=InjectionSource.USER.value,
        ),
        ResolvedEntity(
            source="모름",
            target=UNKNOWN_TRANSLATION,
            entity_type="UNKNOWN",
            source_level=InjectionSource.AUTO.value,
        ),
    ]
    injection_set = EntityInjectionSet(entities=entities, metadata={"test": "value"})

    # Serialize
    data = injection_set.to_dict()
    assert data["count"] == 2
    assert data["metadata"]["test"] == "value"

    # Deserialize
    restored = EntityInjectionSet.from_dict(data)
    assert restored.count == 2
    assert restored.entities[0].source == "정태的"
    assert restored.entities[0].target == "鄭泰義"
    assert restored.entities[1].target == UNKNOWN_TRANSLATION


def test_resolved_entity_serialization():
    """Test ResolvedEntity serialization."""
    entity = ResolvedEntity(
        source="정태的",
        target="鄭泰義",
        entity_type="CHARACTER",
        source_level=InjectionSource.USER.value,
        metadata={"override": True},
    )

    data = entity.to_dict()
    assert data["source"] == "정태的"
    assert data["target"] == "鄭泰義"
    assert data["source_level"] == "USER"

    restored = ResolvedEntity.from_dict(data)
    assert restored.source == "정태的"
    assert restored.target == "鄭泰義"
    assert restored.is_user_override is True


def test_extracted_entity_serialization():
    """Test ExtractedEntity serialization."""
    entity = ExtractedEntity(
        source="정태的",
        entity_type="CHARACTER",
        context="정태的가 왔다.",
        position=0,
    )

    data = entity.to_dict()
    assert data["source"] == "정태的"
    assert data["entity_type"] == "CHARACTER"
    assert data["position"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
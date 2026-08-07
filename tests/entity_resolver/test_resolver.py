"""Tests for Entity Resolver (RM-7.2)."""

import pytest

from core.entity_resolver import (
    EntityResolver,
    EntityInjectionSet,
    ResolvedEntity,
    ExtractedEntity,
    EntityType,
    InjectionSource,
    UNKNOWN_TRANSLATION,
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


def test_resolver_user_override_priority():
    """Test USER override has highest priority."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義"},  # Runtime says 鄭泰義
    })
    user_overrides = {"정태的": "정태的_사용자정의"}  # User says different

    resolver = EntityResolver(runtime=runtime, user_overrides=user_overrides)

    extracted = [ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    assert result.count == 1
    entity = result.entities[0]
    assert entity.source == "정태的"
    assert entity.target == "정태的_사용자정의"
    assert entity.source_level == InjectionSource.USER.value
    assert entity.is_user_override is True


def test_resolver_runtime_fallback():
    """Test RUNTIME resolution when no USER override."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義", "일레이": "伊萊"},
        "glossary": {"신림동": "Sillim-dong"},
    })

    resolver = EntityResolver(runtime=runtime)

    extracted = [
        ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="신림동", entity_type=EntityType.PLACE.value),
    ]
    result = resolver.resolve(extracted)

    assert result.count == 2
    assert result.entities[0].target == "鄭泰義"
    assert result.entities[0].source_level == InjectionSource.RUNTIME.value
    assert result.entities[1].target == "Sillim-dong"
    assert result.entities[1].source_level == InjectionSource.RUNTIME.value


def test_resolver_learning_fallback():
    """Test LEARNING resolution when no USER or RUNTIME."""
    runtime = MockRuntime({})  # Empty runtime
    learning = {"크리스토프": "克里斯托夫"}  # From historical patterns

    resolver = EntityResolver(runtime=runtime, learning_data=learning)

    extracted = [ExtractedEntity(source="크리스토프", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    assert result.count == 1
    entity = result.entities[0]
    assert entity.target == "克里斯托夫"
    assert entity.source_level == InjectionSource.LEARNING.value
    assert entity.metadata.get("source") == "learning"


def test_resolver_auto_unknown():
    """Test AUTO level for unknown entities."""
    runtime = MockRuntime({})
    resolver = EntityResolver(runtime=runtime)

    extracted = [ExtractedEntity(source="모르는사람", entity_type=EntityType.UNKNOWN.value)]
    result = resolver.resolve(extracted)

    assert result.count == 1
    entity = result.entities[0]
    assert entity.target == UNKNOWN_TRANSLATION
    assert entity.source_level == InjectionSource.AUTO.value
    assert entity.metadata.get("unknown") is True
    assert entity.is_known is False


def test_resolver_priority_order():
    """Test full priority: USER > RUNTIME > LEARNING > AUTO."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義_RUNTIME"},
    })
    user_overrides = {"정태的": "鄭泰義_USER"}
    learning = {"정태的": "鄭泰義_LEARNING"}

    resolver = EntityResolver(
        runtime=runtime,
        user_overrides=user_overrides,
        learning_data=learning,
    )

    extracted = [ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    # USER should win
    assert result.entities[0].target == "鄭泰義_USER"
    assert result.entities[0].source_level == InjectionSource.USER.value


def test_resolver_user_override_immutable():
    """Test that USER override cannot be overridden by lower levels."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義_RUNTIME"},
    })
    user_overrides = {"정태的": "鄭泰義_USER"}
    learning = {"정태的": "鄭泰義_LEARNING"}

    resolver = EntityResolver(
        runtime=runtime,
        user_overrides=user_overrides,
        learning_data=learning,
    )

    # Even if we update runtime, USER should still win
    runtime2 = MockRuntime({
        "character": {"정태的": "鄭泰義_NEW_RUNTIME"},
    })
    resolver.update_runtime(runtime2)

    extracted = [ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)

    assert result.entities[0].target == "鄭泰義_USER"
    assert result.entities[0].source_level == InjectionSource.USER.value


def test_resolver_metadata_tracking():
    """Test that resolution metadata is tracked."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義"},
        "glossary": {"용어": "term"},
    })
    user_overrides = {"사용자": "USER_TERM"}
    learning = {"학습": "LEARNING_TERM"}

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

    meta = result.metadata
    assert meta["user_overrides"] == 1
    assert meta["runtime_resolved"] == 1
    assert meta["learning_resolved"] == 1
    assert meta["auto_unknown"] == 1


def test_resolver_add_remove_user_override():
    """Test adding and removing user overrides dynamically."""
    runtime = MockRuntime({})
    resolver = EntityResolver(runtime=runtime)

    # Initially unknown
    extracted = [ExtractedEntity(source="새이름", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)
    assert result.entities[0].target == UNKNOWN_TRANSLATION

    # Add user override
    resolver.add_user_override("새이름", "새이름_번역")
    result = resolver.resolve(extracted)
    assert result.entities[0].target == "새이름_번역"
    assert result.entities[0].source_level == InjectionSource.USER.value

    # Remove user override
    resolver.remove_user_override("새이름")
    result = resolver.resolve(extracted)
    assert result.entities[0].target == UNKNOWN_TRANSLATION


def test_resolver_update_learning():
    """Test updating learning data."""
    runtime = MockRuntime({})
    resolver = EntityResolver(runtime=runtime)

    extracted = [ExtractedEntity(source="학습이름", entity_type=EntityType.CHARACTER.value)]
    result = resolver.resolve(extracted)
    assert result.entities[0].target == UNKNOWN_TRANSLATION

    # Add learning data
    resolver.update_learning({"학습이름": "학습_번역"})
    result = resolver.resolve(extracted)
    assert result.entities[0].target == "학습_번역"
    assert result.entities[0].source_level == InjectionSource.LEARNING.value


def test_resolver_multiple_entities():
    """Test resolving multiple entities at once."""
    runtime = MockRuntime({
        "character": {"정태的": "鄭泰義", "일레이": "伊萊"},
        "scene": {"서울": "Seoul"},
    })

    resolver = EntityResolver(runtime=runtime)

    extracted = [
        ExtractedEntity(source="정태的", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="일레이", entity_type=EntityType.CHARACTER.value),
        ExtractedEntity(source="서울", entity_type=EntityType.PLACE.value),
        ExtractedEntity(source="모르는곳", entity_type=EntityType.UNKNOWN.value),
    ]
    result = resolver.resolve(extracted)

    assert result.count == 4
    known = result.get_known_entities()
    unknown = result.get_unknown_entities()

    assert len(known) == 3
    assert len(unknown) == 1
    assert unknown[0].source == "모르는곳"


def test_injection_set_methods():
    """Test EntityInjectionSet helper methods."""
    entities = [
        ResolvedEntity(source="정태的", target="鄭泰義", source_level=InjectionSource.USER.value),
        ResolvedEntity(source="일레이", target="伊萊", source_level=InjectionSource.RUNTIME.value),
        ResolvedEntity(source="모름", target=UNKNOWN_TRANSLATION, source_level=InjectionSource.AUTO.value),
    ]
    injection_set = EntityInjectionSet(entities=entities)

    assert injection_set.count == 3
    assert len(injection_set.get_known_entities()) == 2
    assert len(injection_set.get_unknown_entities()) == 1
    assert injection_set.get_by_source("정태的").target == "鄭泰義"
    assert injection_set.get_by_source("존재안함") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
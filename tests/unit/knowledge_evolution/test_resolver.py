"""Tests for RM-7.0 KnowledgeResolver."""

import tempfile

from core.knowledge_evolution.models import (
    EntityType,
    KnowledgeEntity,
    PriorityLevel,
)
from core.knowledge_evolution.resolver import KnowledgeResolver
from core.knowledge_evolution.store import KnowledgeStore


class TestKnowledgeResolver:
    def test_resolve_finds_user_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
                locked=True,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")

            resolver = KnowledgeResolver(store)
            result = resolver.resolve("정태의")
            assert result is not None
            assert result.canonical == "鄭泰義"
            assert result.priority == PriorityLevel.USER

    def test_user_priority_over_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            user_e = KnowledgeEntity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            rt_e = KnowledgeEntity(
                source="정태의",
                canonical="鄭太義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.RUNTIME,
            )
            store.save_entities([rt_e], PriorityLevel.RUNTIME, "characters")
            store.save_entities([user_e], PriorityLevel.USER, "characters")

            resolver = KnowledgeResolver(store)
            result = resolver.resolve("정태의")
            assert result is not None
            assert result.canonical == "鄭泰義"
            assert result.priority == PriorityLevel.USER

    def test_resolve_canonical_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            resolver = KnowledgeResolver(store)
            assert resolver.resolve_canonical("nonexistent") == "nonexistent"

    def test_resolve_with_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")

            resolver = KnowledgeResolver(store)
            entity, pri = resolver.resolve_with_priority("A")
            assert entity is not None
            assert pri == PriorityLevel.USER

        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            resolver = KnowledgeResolver(store)
            assert resolver.resolve_with_priority("X") is None

    def test_alias_resolved_before_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="鄭泰義",
                canonical="정태의",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")
            from core.knowledge_evolution.models import AliasEntry
            a = AliasEntry(alias="泰義", target="鄭泰義")
            store.save_aliases([a], PriorityLevel.USER)

            resolver = KnowledgeResolver(store)
            result = resolver.resolve("泰義")
            assert result is not None
            assert result.source == "鄭泰義"
            assert result.canonical == "정태의"

    def test_list_all_canonicals(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e1 = KnowledgeEntity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            e2 = KnowledgeEntity(
                source="B",
                canonical="Beta",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.RUNTIME,
            )
            store.save_entities([e1], PriorityLevel.USER, "characters")
            store.save_entities([e2], PriorityLevel.RUNTIME, "characters")

            resolver = KnowledgeResolver(store)
            canonicals = resolver.list_all_canonicals()
            assert "Alpha" in canonicals
            assert "Beta" in canonicals

    def test_source_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="X",
                canonical="Y",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.RUNTIME,
            )
            store.save_entities([e], PriorityLevel.RUNTIME, "characters")

            resolver = KnowledgeResolver(store)
            assert resolver.source_priority("X") == PriorityLevel.RUNTIME
            assert resolver.source_priority("Z") is None

    def test_resolve_with_entity_type_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e_char = KnowledgeEntity(
                source="test",
                canonical="Test",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            e_term = KnowledgeEntity(
                source="term",
                canonical="TermTranslate",
                entity_type=EntityType.TERM,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e_char], PriorityLevel.USER, "characters")
            store.save_entities([e_term], PriorityLevel.USER, "glossary")

            resolver = KnowledgeResolver(store)
            assert resolver.resolve("term", EntityType.TERM) is not None
            assert resolver.resolve("term", EntityType.CHARACTER) is None

    def test_invalidate_reloads_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")

            resolver = KnowledgeResolver(store)
            assert resolver.resolve("A").canonical == "Alpha"

            e2 = KnowledgeEntity(
                source="A",
                canonical="AlphaPrime",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e2], PriorityLevel.USER, "characters")
            resolver.invalidate()
            assert resolver.resolve("A").canonical == "AlphaPrime"
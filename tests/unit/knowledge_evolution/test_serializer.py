"""Tests for RM-7.0 serializer."""

import tempfile

from core.knowledge_evolution.manager import KnowledgeManager
from core.knowledge_evolution.models import (
    EntityType,
    EvolutionReport,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
)
from core.knowledge_evolution.serializer import (
    KnowledgeSerializer,
    aliases_to_markdown,
    entities_to_markdown,
    report_to_markdown,
    to_json,
)
from core.knowledge_evolution.store import KnowledgeStore


class TestSerializerFunctions:
    def test_to_json_entity(self):
        e = KnowledgeEntity(
            source="정태의",
            canonical="鄭泰義",
            entity_type=EntityType.CHARACTER,
            priority=PriorityLevel.USER,
        )
        output = to_json(e)
        assert '"source": "정태의"' in output
        assert '"canonical": "鄭泰義"' in output

    def test_to_json_list(self):
        entities = [
            KnowledgeEntity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            ),
        ]
        output = to_json(entities)
        assert '"source": "A"' in output
        assert '"canonical": "Alpha"' in output

    def test_entities_to_markdown(self):
        entities = [
            KnowledgeEntity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
                locked=True,
            ),
        ]
        md = entities_to_markdown(entities, "Test Entities")
        assert "鄭泰義" in md
        assert "정태의" in md
        assert "LOCKED" in md
        assert "Test Entities" in md

    def test_aliases_to_markdown(self):
        from core.knowledge_evolution.models import AliasEntry
        aliases = [AliasEntry(alias="泰", target="鄭泰", confidence=0.9)]
        md = aliases_to_markdown(aliases, "Test Aliases")
        assert "泰" in md
        assert "鄭泰" in md
        assert "0.90" in md

    def test_aliases_to_markdown_empty(self):
        md = aliases_to_markdown([], "Empty")
        assert "No aliases defined" in md

    def test_report_to_markdown(self):
        from core.knowledge_evolution.models import EvolutionReport
        report = EvolutionReport(
            new_entities=5,
            updated_entities=3,
            conflicts=2,
            total_entities=10,
            total_candidates=3,
        )
        entities = [
            KnowledgeEntity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            ),
        ]
        md = report_to_markdown(report, entities, [])
        assert "new entities: 5" in md.lower() or "New entities: 5" in md
        assert "Alpha" in md
        assert "total entities: 10" in md.lower() or "Total entities: 10" in md


class TestKnowledgeSerializer:
    def test_to_json_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            from core.knowledge_evolution.store import KnowledgeStore
            from core.knowledge_evolution.resolver import KnowledgeResolver

            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")
            resolver = KnowledgeResolver(store)

            serializer = KnowledgeSerializer(store, resolver)
            output = serializer.to_json()
            assert '"version": "rm-7.0"' in output
            assert '"鄭泰義"' in output

    def test_to_markdown_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            from core.knowledge_evolution.store import KnowledgeStore
            from core.knowledge_evolution.resolver import KnowledgeResolver

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

            serializer = KnowledgeSerializer(store, resolver)
            md = serializer.to_markdown()
            assert "鄭泰義" in md
            assert "정태의" in md
            assert "RM-7.0" in md

    def test_to_markdown_with_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            from core.knowledge_evolution.store import KnowledgeStore
            from core.knowledge_evolution.resolver import KnowledgeResolver

            store = KnowledgeStore(store_root=tmp)
            c = LearningCandidate(
                source="x",
                canonical="X",
                entity_type=EntityType.CHARACTER,
                confidence=0.5,
            )
            store.save_candidates([c])
            resolver = KnowledgeResolver(store)

            serializer = KnowledgeSerializer(store, resolver)
            md = serializer.to_markdown()
            assert "PENDING" in md

    def test_to_report_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            from core.knowledge_evolution.store import KnowledgeStore
            from core.knowledge_evolution.resolver import KnowledgeResolver

            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="test",
                canonical="Test",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")
            resolver = KnowledgeResolver(store)

            serializer = KnowledgeSerializer(store, resolver)
            report = serializer.to_report()
            assert "Knowledge Evolution Report" in report
            assert "USER:" in report
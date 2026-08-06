"""Tests for RM-7.0 KnowledgeStore."""

import json
import tempfile
from pathlib import Path

from core.knowledge_evolution.models import (
    AliasEntry,
    CandidateStatus,
    EntityType,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
)
from core.knowledge_evolution.store import KnowledgeStore


class TestKnowledgeStore:
    def test_ensure_dirs_creates_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            store.ensure_dirs()
            assert Path(tmp, "user").is_dir()
            assert Path(tmp, "runtime").is_dir()
            assert Path(tmp, "learning").is_dir()

    def test_save_and_load_entities(self):
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
            loaded = store.load_entities(PriorityLevel.USER, "characters")
            assert len(loaded) == 1
            assert loaded[0].source == "정태의"
            assert loaded[0].canonical == "鄭泰義"

    def test_load_empty_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            loaded = store.load_entities(PriorityLevel.USER, "characters")
            assert loaded == []

    def test_save_glossary_entities(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="무협",
                canonical="武俠",
                entity_type=EntityType.TERM,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "glossary")
            loaded = store.load_entities(PriorityLevel.USER, "glossary")
            assert len(loaded) == 1
            assert loaded[0].source == "무협"

    def test_save_load_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            a = AliasEntry(alias="泰義", target="鄭泰義", confidence=0.95)
            store.save_aliases([a], PriorityLevel.USER)
            loaded = store.load_aliases(PriorityLevel.USER)
            assert len(loaded) == 1
            assert loaded[0].alias == "泰義"
            assert loaded[0].target == "鄭泰義"

    def test_save_load_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            c = LearningCandidate(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.82,
            )
            store.save_candidates([c])
            loaded = store.load_candidates()
            assert len(loaded) == 1
            assert loaded[0].source == "일레이"
            assert loaded[0].confidence == 0.82

    def test_multiple_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            user_e = KnowledgeEntity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            rt_e = KnowledgeEntity(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.RUNTIME,
            )
            store.save_entities([user_e], PriorityLevel.USER, "characters")
            store.save_entities([rt_e], PriorityLevel.RUNTIME, "characters")

            assert store.entity_count(PriorityLevel.USER) == 1
            assert store.entity_count(PriorityLevel.RUNTIME) == 1

            sources = store.list_all_sources()
            assert "정태의" in sources["user"]
            assert "일레이" in sources["runtime"]

    def test_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            e = KnowledgeEntity(
                source="test",
                canonical="Test",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            store.save_entities([e], PriorityLevel.USER, "characters")
            snap = store.snapshot()
            assert snap["user_characters"] == 1
            assert snap["runtime_characters"] == 0
            assert snap["candidates"] == 0

    def test_candidate_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(store_root=tmp)
            c = LearningCandidate(
                source="x",
                canonical="X",
                entity_type=EntityType.CHARACTER,
            )
            store.save_candidates([c])
            assert store.candidate_count() == 1
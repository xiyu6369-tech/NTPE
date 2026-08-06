"""Tests for RM-7.0 KnowledgeEvolution models."""

import json

import pytest

from core.knowledge_evolution.models import (
    AliasEntry,
    CandidateStatus,
    ConflictRecord,
    EntityType,
    EvolutionReport,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
    Severity,
    PRIORITY_ORDER,
)


class TestPriorityLevel:
    def test_ordering(self):
        assert PriorityLevel.USER < PriorityLevel.RUNTIME
        assert PriorityLevel.RUNTIME < PriorityLevel.LEARNING
        assert PriorityLevel.LEARNING < PriorityLevel.AUTO

    def test_priority_order_list(self):
        assert PRIORITY_ORDER == [
            PriorityLevel.USER,
            PriorityLevel.RUNTIME,
            PriorityLevel.LEARNING,
            PriorityLevel.AUTO,
        ]

    def test_from_string(self):
        assert PriorityLevel("USER") == PriorityLevel.USER
        assert PriorityLevel("RUNTIME") == PriorityLevel.RUNTIME
        assert PriorityLevel("LEARNING") == PriorityLevel.LEARNING


class TestKnowledgeEntity:
    def test_create(self):
        e = KnowledgeEntity(
            source="정태의",
            canonical="鄭泰義",
            entity_type=EntityType.CHARACTER,
            priority=PriorityLevel.USER,
            locked=True,
        )
        assert e.source == "정태의"
        assert e.canonical == "鄭泰義"
        assert e.entity_type == EntityType.CHARACTER
        assert e.priority == PriorityLevel.USER
        assert e.locked is True
        assert e.is_locked is True
        assert e.confidence == 1.0
        assert e.version == 1

    def test_user_always_locked(self):
        e = KnowledgeEntity(
            source="a",
            canonical="A",
            entity_type=EntityType.CHARACTER,
            priority=PriorityLevel.USER,
            locked=False,
        )
        assert e.is_locked is True

    def test_learning_not_locked(self):
        e = KnowledgeEntity(
            source="a",
            canonical="A",
            entity_type=EntityType.CHARACTER,
            priority=PriorityLevel.LEARNING,
            locked=False,
        )
        assert e.is_locked is False

    def test_roundtrip(self):
        e = KnowledgeEntity(
            source="일레이",
            canonical="伊萊",
            entity_type=EntityType.CHARACTER,
            priority=PriorityLevel.RUNTIME,
            locked=False,
            confidence=0.85,
            metadata={"novel": "some_novel"},
        )
        data = e.to_dict()
        restored = KnowledgeEntity.from_dict(data)
        assert restored.source == e.source
        assert restored.canonical == e.canonical
        assert restored.entity_type == e.entity_type
        assert restored.priority == e.priority
        assert restored.confidence == e.confidence
        assert restored.metadata == e.metadata

    def test_immutable(self):
        from dataclasses import FrozenInstanceError
        import pytest
        e = KnowledgeEntity(source="x", canonical="X", entity_type=EntityType.CHARACTER)
        with pytest.raises(FrozenInstanceError):
            e.source = "y"


class TestAliasEntry:
    def test_create(self):
        a = AliasEntry(alias="泰義", target="鄭泰義", confidence=0.95)
        assert a.alias == "泰義"
        assert a.target == "鄭泰義"
        assert a.confidence == 0.95

    def test_roundtrip(self):
        a = AliasEntry(alias="A", target="B", confidence=0.8, source="test")
        data = a.to_dict()
        restored = AliasEntry.from_dict(data)
        assert restored.alias == a.alias
        assert restored.target == a.target
        assert restored.confidence == a.confidence


class TestConflictRecord:
    def test_create(self):
        c = ConflictRecord(
            source="정태의",
            expected="鄭泰義",
            observed="鄭太義",
            severity=Severity.HIGH,
        )
        assert c.source == "정태의"
        assert c.expected == "鄭泰義"
        assert c.observed == "鄭太義"
        assert c.severity == Severity.HIGH
        assert c.resolved is False
        assert c.resolution is None

    def test_resolved(self):
        c = ConflictRecord(
            source="정태의",
            expected="鄭泰義",
            observed="鄭太義",
            severity=Severity.HIGH,
            resolution="鄭泰義",
        )
        assert c.resolved is True

    def test_roundtrip(self):
        c = ConflictRecord(
            source="정태의",
            expected="鄭泰義",
            observed="鄭太義",
            severity=Severity.HIGH,
        )
        data = c.to_dict()
        restored = ConflictRecord.from_dict(data)
        assert restored.source == c.source
        assert restored.expected == c.expected
        assert restored.severity == c.severity


class TestEvolutionReport:
    def test_empty(self):
        r = EvolutionReport()
        assert r.has_changes is False

    def test_with_changes(self):
        r = EvolutionReport(new_entities=5, updated_entities=3, conflicts=2)
        assert r.has_changes is True

    def test_roundtrip(self):
        r = EvolutionReport(
            new_entities=5,
            updated_entities=3,
            conflicts=2,
            promoted_candidates=1,
            rejected_candidates=0,
            total_entities=10,
            total_candidates=3,
            details={"samples": []},
        )
        data = r.to_dict()
        restored = EvolutionReport.from_dict(data)
        assert restored.new_entities == 5
        assert restored.updated_entities == 3
        assert restored.conflicts == 2


class TestLearningCandidate:
    def test_create(self):
        c = LearningCandidate(
            source="일레이",
            canonical="伊萊",
            entity_type=EntityType.CHARACTER,
            confidence=0.82,
            occurrence_count=1,
        )
        assert c.source == "일레이"
        assert c.canonical == "伊萊"
        assert c.confidence == 0.82
        assert c.status == CandidateStatus.PENDING

    def test_roundtrip(self):
        c = LearningCandidate(
            source="x",
            canonical="X",
            entity_type=EntityType.TERM,
            confidence=0.7,
            occurrence_count=3,
            context_hints=["chapter 1", "chapter 3"],
            status=CandidateStatus.PENDING,
        )
        data = c.to_dict()
        restored = LearningCandidate.from_dict(data)
        assert restored.source == "x"
        assert restored.confidence == 0.7
        assert restored.occurrence_count == 3
        assert restored.context_hints == ["chapter 1", "chapter 3"]
        assert restored.status == CandidateStatus.PENDING
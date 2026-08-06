"""Tests for RM-7.0 KnowledgeManager."""

import tempfile

from core.knowledge_evolution.manager import KnowledgeManager
from core.knowledge_evolution.models import (
    CandidateStatus,
    EntityType,
    LearningCandidate,
    PriorityLevel,
)


class TestKnowledgeManager:
    def test_add_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            e = mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            assert e.source == "정태의"
            assert e.canonical == "鄭泰義"
            assert e.priority == PriorityLevel.USER

    def test_get_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            e = mgr.get_entity("정태의")
            assert e is not None
            assert e.canonical == "鄭泰義"

    def test_get_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            assert mgr.get_canonical("정태의") == "鄭泰義"
            assert mgr.get_canonical("nonexistent") == "nonexistent"

    def test_update_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="test",
                canonical="Old",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.LEARNING,
                locked=False,
            )
            updated = mgr.update_entity(
                source="test",
                canonical="New",
                confidence=0.9,
            )
            assert updated is not None
            assert updated.canonical == "New"
            assert updated.confidence == 0.9
            assert updated.version == 2

    def test_update_locked_entity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="test",
                canonical="Locked",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
                locked=True,
            )
            updated = mgr.update_entity(source="test", canonical="Changed")
            assert updated is None

    def test_delete_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="deletable",
                canonical="Del",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.LEARNING,
                locked=False,
            )
            assert mgr.delete_entity("deletable") is True
            assert mgr.get_entity("deletable") is None

    def test_delete_locked_entity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="locked_src",
                canonical="LockedVal",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
                locked=True,
            )
            assert mgr.delete_entity("locked_src") is False
            assert mgr.get_entity("locked_src") is not None

    def test_lock_unlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="x",
                canonical="X",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.LEARNING,
                locked=False,
            )
            assert mgr.lock_entity("x") is True
            e = mgr.get_entity("x")
            assert e.locked is True

            assert mgr.unlock_entity("x") is True
            e = mgr.get_entity("x")
            assert e.locked is False

    def test_unlock_user_entity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="x",
                canonical="X",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            assert mgr.unlock_entity("x") is False

    def test_alias_management(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            a = mgr.add_alias(
                alias="泰義",
                target="鄭泰義",
                confidence=0.95,
                priority=PriorityLevel.USER,
            )
            assert a.alias == "泰義"

            mgr.add_entity(
                source="鄭泰義",
                canonical="정태의",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )

            result = mgr.resolve_alias("泰義")
            assert result is not None

    def test_add_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            c = mgr.add_candidate(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.82,
            )
            assert c.source == "일레이"
            assert c.confidence == 0.82
            assert c.occurrence_count == 1

    def test_add_duplicate_candidate_boosts_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_candidate(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.5,
            )
            c2 = mgr.add_candidate(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.9,
            )
            assert c2.occurrence_count == 2
            assert c2.confidence == 0.9

    def test_candidate_blocked_by_existing_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="exists",
                canonical="Exists",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            with tempfile.TemporaryDirectory() as tmp2:
                tmp2_manager = KnowledgeManager(store_root=tmp2)
                mgr2 = tmp2_manager
                mgr2.add_entity(
                    source="exists",
                    canonical="Exists",
                    entity_type=EntityType.CHARACTER,
                    priority=PriorityLevel.USER,
                )
                import pytest
                with pytest.raises(ValueError, match="Entity already exists"):
                    mgr2.add_candidate(source="exists", canonical="X")

    def test_promote_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_candidate(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.82,
            )
            promoted = mgr.promote_candidate("일레이")
            assert promoted is not None
            assert promoted.canonical == "伊萊"
            assert promoted.priority == PriorityLevel.LEARNING

    def test_reject_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_candidate(
                source="x",
                canonical="X",
                entity_type=EntityType.CHARACTER,
            )
            assert mgr.reject_candidate("x") is True
            candidates = mgr.list_candidates()
            rejected = [c for c in candidates if c.source == "x"]
            assert all(c.status == CandidateStatus.REJECTED for c in rejected)

    def test_detect_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            conflict = mgr.detect_conflict("정태의", "鄭太義")
            assert conflict is not None
            assert conflict.expected == "鄭泰義"
            assert conflict.observed == "鄭太義"

    def test_detect_conflict_no_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            conflict = mgr.detect_conflict("정태의", "鄭泰義")
            assert conflict is None

    def test_detect_conflict_unknown_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            assert mgr.detect_conflict("nonexistent", "X") is None

    def test_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            snap = mgr.snapshot()
            assert snap["user_characters"] == 1

    def test_add_glossary_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="무협",
                canonical="武俠",
                entity_type=EntityType.TERM,
                priority=PriorityLevel.USER,
            )
            e = mgr.get_entity("무협")
            assert e is not None
            assert e.canonical == "武俠"

    def test_update_entity_moving_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="test",
                canonical="Test",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.LEARNING,
            )
            updated = mgr.update_entity(
                source="test",
                entity_type=EntityType.TERM,
            )
            assert updated is not None
            assert updated.entity_type == EntityType.TERM

    def test_delete_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            assert mgr.delete_entity("nonexistent") is False
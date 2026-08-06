"""Tests for RM-7.0 KnowledgeEvolution engine."""

import tempfile

from core.knowledge_evolution.evolution import KnowledgeEvolution
from core.knowledge_evolution.manager import KnowledgeManager
from core.knowledge_evolution.models import (
    CandidateStatus,
    EntityType,
    PriorityLevel,
)


class TestKnowledgeEvolution:
    def test_learn_new_term_creates_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            ev = KnowledgeEvolution(mgr)

            result = ev.learn_term(
                source="일레이",
                canonical="伊萊",
                entity_type=EntityType.CHARACTER,
                confidence=0.82,
            )
            assert result["status"] == "new"
            assert result["source"] == "일레이"
            assert result["canonical"] == "伊萊"
            assert result["confidence"] == 0.82

    def test_learn_term_reinforces_existing_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            ev = KnowledgeEvolution(mgr)

            ev.learn_term("x", "X", EntityType.CHARACTER, 0.5)
            result = ev.learn_term("x", "X", EntityType.CHARACTER, 0.5)
            assert result["status"] == "reinforced"

    def test_learn_term_skips_existing_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev = KnowledgeEvolution(mgr)
            result = ev.learn_term("정태의", "鄭泰義", EntityType.CHARACTER)
            assert result["status"] == "exists"

    def test_verify_term_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev = KnowledgeEvolution(mgr)
            result = ev.verify_term("정태의", "鄭泰義")
            assert result is None

    def test_verify_term_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev = KnowledgeEvolution(mgr)
            result = ev.verify_term("정태의", "鄭太義")
            assert result is not None
            assert result["status"] == "conflict"
            assert result["expected"] == "鄭泰義"
            assert result["observed"] == "鄭太義"

    def test_scan_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            ev = KnowledgeEvolution(mgr)

            terms = [
                {"source": "일레이", "canonical": "伊萊", "confidence": 0.82},
                {"source": "정수", "canonical": "鄭秀", "confidence": 0.7},
            ]
            report = ev.scan_terms(terms)
            assert report.new_entities == 2
            assert report.conflicts == 0

    def test_scan_terms_with_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="정태의",
                canonical="鄭泰義",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev = KnowledgeEvolution(mgr)
            terms = [
                {"source": "정태의", "canonical": "鄭太義", "discover": False},
            ]
            report = ev.scan_terms(terms)
            assert report.conflicts == 1

    def test_promote_all_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            ev = KnowledgeEvolution(mgr)

            ev.learn_term("A", "Alpha", EntityType.CHARACTER, 0.9)
            ev.learn_term("B", "Beta", EntityType.CHARACTER, 0.3)
            for _ in range(3):
                ev.learn_term("A", "Alpha", EntityType.CHARACTER, 0.9)

            report = ev.promote_all_candidates(
                min_confidence=0.6,
                min_occurrences=2,
            )
            assert report.promoted_candidates == 1
            assert report.rejected_candidates == 1

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            ev = KnowledgeEvolution(mgr)

            mgr.add_entity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev.learn_term("B", "Beta", EntityType.CHARACTER, 0.5)
            summary = ev.summary()
            assert summary["total_entities"] == 1
            assert summary["candidates"] == 1

    def test_conflicts_accumulate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = KnowledgeManager(store_root=tmp)
            mgr.add_entity(
                source="A",
                canonical="Alpha",
                entity_type=EntityType.CHARACTER,
                priority=PriorityLevel.USER,
            )
            ev = KnowledgeEvolution(mgr)
            ev.verify_term("A", "Beta")
            ev.verify_term("A", "Gamma")
            assert len(ev.conflicts) == 2
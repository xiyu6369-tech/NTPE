"""Tests for entity_normalization conflict module."""

import pytest

from core.entity_normalization.conflict import (
    ConflictDetector,
    ConflictResolver,
    ConflictCandidate,
    build_candidates_from_sources,
)
from core.entity_normalization.models import (
    EntityType,
    ConflictSeverity,
    ResolutionSource,
    ConflictRecord,
)


class TestConflictCandidate:
    def test_creation(self):
        candidate = ConflictCandidate(
            translation="鄭泰義",
            source=ResolutionSource.USER,
            confidence=1.0,
        )
        assert candidate.translation == "鄭泰義"
        assert candidate.source == ResolutionSource.USER
        assert candidate.confidence == 1.0


class TestConflictDetector:
    def test_no_conflict_single_candidate(self):
        detector = ConflictDetector()
        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        assert len(conflicts) == 0

    def test_no_conflict_same_translation(self):
        detector = ConflictDetector()
        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
            ConflictCandidate("鄭泰義", ResolutionSource.RUNTIME),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        assert len(conflicts) == 0

    def test_conflict_detected(self):
        detector = ConflictDetector()
        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
            ConflictCandidate("鄭太義", ResolutionSource.RUNTIME),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict.source == "正泰義"
        assert set(conflict.candidates) == {"鄭泰義", "鄭太義"}

    def test_high_severity_user_vs_runtime(self):
        detector = ConflictDetector()
        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
            ConflictCandidate("鄭太義", ResolutionSource.RUNTIME),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        assert conflicts[0].severity == ConflictSeverity.HIGH

    def test_medium_severity_learning_vs_auto(self):
        detector = ConflictDetector()
        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.LEARNING),
            ConflictCandidate("鄭太義", ResolutionSource.AUTO),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        assert conflicts[0].severity == ConflictSeverity.MEDIUM


class TestConflictResolver:
    def test_resolve_user_wins(self):
        resolver = ConflictResolver()
        detector = ConflictDetector()

        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
            ConflictCandidate("鄭太義", ResolutionSource.RUNTIME),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        resolved = resolver.resolve_with_priority(conflicts[0], candidates)

        assert resolved.resolution == "鄭泰義"
        assert resolved.resolution_source == ResolutionSource.USER

    def test_resolve_runtime_wins_over_learning(self):
        resolver = ConflictResolver()
        detector = ConflictDetector()

        candidates = [
            ConflictCandidate("鄭太義", ResolutionSource.RUNTIME),
            ConflictCandidate("鄭泰義", ResolutionSource.LEARNING),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        resolved = resolver.resolve_with_priority(conflicts[0], candidates)

        assert resolved.resolution == "鄭太義"
        assert resolved.resolution_source == ResolutionSource.RUNTIME

    def test_resolve_learning_wins_over_auto(self):
        resolver = ConflictResolver()
        detector = ConflictDetector()

        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.LEARNING),
            ConflictCandidate("鄭太義", ResolutionSource.AUTO),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        resolved = resolver.resolve_with_priority(conflicts[0], candidates)

        assert resolved.resolution == "鄭泰義"
        assert resolved.resolution_source == ResolutionSource.LEARNING

    def test_get_resolution(self):
        resolver = ConflictResolver()
        detector = ConflictDetector()

        candidates = [
            ConflictCandidate("鄭泰義", ResolutionSource.USER),
            ConflictCandidate("鄭太義", ResolutionSource.RUNTIME),
        ]
        conflicts = detector.detect("正泰義", EntityType.CHARACTER, candidates)
        resolved = resolver.resolve_with_priority(conflicts[0], candidates)

        retrieved = resolver.get_resolution("正泰義")
        assert retrieved is not None
        assert retrieved.resolution == "鄭泰義"


class TestBuildCandidatesFromSources:
    def test_all_sources(self):
        candidates = build_candidates_from_sources(
            source="正泰義",
            entity_type=EntityType.CHARACTER,
            user_override="鄭泰義",
            runtime_translation="鄭太義",
            learning_translation="鄭泰義",
            auto_translation="正泰義",
        )
        assert len(candidates) == 4
        sources = [c.source for c in candidates]
        assert ResolutionSource.USER in sources
        assert ResolutionSource.RUNTIME in sources
        assert ResolutionSource.LEARNING in sources
        assert ResolutionSource.AUTO in sources

    def test_user_only(self):
        candidates = build_candidates_from_sources(
            source="正泰義",
            entity_type=EntityType.CHARACTER,
            user_override="鄭泰義",
        )
        assert len(candidates) == 1
        assert candidates[0].source == ResolutionSource.USER


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
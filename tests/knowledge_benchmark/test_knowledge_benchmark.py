"""Test suite for Knowledge Benchmark - aligned with RM-5.8.2 models.

All tests are offline and deterministic.
"""
import pytest
import json
from pathlib import Path

from core.knowledge_benchmark.models import (
    BenchmarkMetadata, BenchmarkResult, EntityType, DifficultyTier,
    MetricName, MetricScore, EntityMatchResult, ExtractionComparison,
    ExtractorScore, OverallScore, Scorecard, Grade,
)
from core.knowledge_benchmark.errors import (
    BenchmarkError, GoldenDatasetError, ComparisonError,
)
from core.knowledge_benchmark.metrics.accuracy import EntityMatcher, MatchType
from core.knowledge_benchmark.metrics import (
    PrecisionMetric, RecallMetric, F1ScoreMetric,
    ConfidenceCalibrationMetric, SchemaComplianceMetric,
)
from core.knowledge_benchmark.scorer import BenchmarkScorer, ScorerConfig, create_scorer
from core.knowledge_benchmark.comparison import (
    ComparisonEngine, ComparisonConfig, create_comparison_engine,
)


class TestEntityType:
    def test_values(self):
        assert EntityType.CHARACTER == "character"
        assert EntityType.GLOSSARY == "glossary"


class TestDifficultyTier:
    def test_values(self):
        assert DifficultyTier.EASY == "easy"
        assert DifficultyTier.MEDIUM == "medium"
        assert DifficultyTier.HARD == "hard"


class TestMetricName:
    def test_values(self):
        assert MetricName.PRECISION == "precision"
        assert MetricName.RECALL == "recall"
        assert MetricName.F1_SCORE == "f1_score"
        assert MetricName.ECE == "ece"


class TestMetricScore:
    def test_creation(self):
        ms = MetricScore(
            metric_name=MetricName.PRECISION,
            value=0.85,
            target=0.80,
            passed=True,
        )
        assert ms.metric_name == MetricName.PRECISION
        assert ms.value == 0.85
        assert ms.target == 0.80
        assert ms.passed is True

    def test_immutable(self):
        ms = MetricScore(
            metric_name=MetricName.F1_SCORE,
            value=0.5,
            target=0.8,
            passed=False,
        )
        with pytest.raises(Exception):
            ms.value = 1.0  # frozen


class TestEntityMatchResult:
    def test_creation(self):
        mr = EntityMatchResult(
            golden_entity_id="g1",
            predicted_entity_id="p1",
            matched=True,
            match_type=MatchType.EXACT.value,
            similarity_score=0.99,
        )
        assert mr.golden_entity_id == "g1"
        assert mr.predicted_entity_id == "p1"
        assert mr.matched is True
        assert mr.match_type == MatchType.EXACT.value

    def test_unmatched(self):
        mr = EntityMatchResult(
            golden_entity_id="g1",
            predicted_entity_id=None,
            matched=False,
            match_type=MatchType.NONE.value,
        )
        assert mr.matched is False
        assert mr.predicted_entity_id is None


class TestMatchTypeEnum:
    def test_values(self):
        assert MatchType.EXACT == "exact"
        assert MatchType.SEMANTIC == "semantic"
        assert MatchType.NONE == "none"


class TestEntityMatcher:
    def test_initialization(self):
        matcher = EntityMatcher()
        assert matcher.similarity_threshold == 0.85

    def test_match_entities_returns_list(self):
        matcher = EntityMatcher()
        golden = [{"id": "g1", "name": "Alice"}]
        predicted = [{"id": "g1", "name": "Alice", "confidence": 0.95}]
        results = matcher.match_entities(
            golden, predicted, EntityType.CHARACTER
        )
        assert isinstance(results, list)
        assert all(isinstance(r, EntityMatchResult) for r in results)


class TestBenchmarkMetadata:
    def test_creation(self):
        md = BenchmarkMetadata(
            benchmark_id="test_001",
            benchmark_version="1.0",
            golden_dataset_version="1.0",
        )
        assert md.benchmark_id == "test_001"
        assert md.benchmark_version == "1.0"


class TestScorecard:
    def test_creation(self):
        md = BenchmarkMetadata(
            benchmark_id="test_001", benchmark_version="1.0",
            golden_dataset_version="1.0",
        )
        sc = Scorecard(metadata=md, overall=OverallScore())
        assert sc.metadata.benchmark_id == "test_001"
        assert sc.overall.overall_score == 0.0


class TestScorerCreation:
    def test_factory(self):
        scorer = create_scorer()
        assert scorer is not None
        assert isinstance(scorer, BenchmarkScorer)


class TestComparisonEngineCreation:
    def test_factory(self):
        engine = create_comparison_engine()
        assert engine is not None
        assert isinstance(engine, ComparisonEngine)


class TestComparisonEngineCreateComparison:
    """Regression tests for ComparisonEngine.create_comparison() end-to-end."""

    def test_create_comparison_matched_entities(self):
        engine = create_comparison_engine()
        golden = [{"id": "g1", "name": "Alice", "type": "character"}]
        predicted = [{"id": "g1", "name": "Alice", "type": "character", "confidence": 0.95}]

        comp = engine.create_comparison(
            extractor_type=EntityType.CHARACTER,
            golden_entities=golden,
            predicted_entities=predicted,
            difficulty_tier=DifficultyTier.EASY,
        )

        assert comp.extractor_type == EntityType.CHARACTER
        assert comp.difficulty_tier == DifficultyTier.EASY
        assert len(comp.matched_entities) > 0
        assert len(comp.golden_entities) == 1
        assert len(comp.predicted_entities) == 1
        assert len(comp.matches) > 0

        match_result = comp.matches[0]
        assert isinstance(match_result, EntityMatchResult)
        assert match_result.matched is True
        assert match_result.golden_entity_id == "g1"
        assert match_result.predicted_entity_id == "g1"
        assert hasattr(match_result, "similarity_score")
        assert hasattr(match_result, "field_matches")

    def test_create_comparison_unmatched_golden(self):
        engine = create_comparison_engine()
        golden = [{"id": "g1", "name": "Alice"}]
        predicted = [{"id": "p1", "name": "Bob", "confidence": 0.95}]

        comp = engine.create_comparison(
            extractor_type=EntityType.CHARACTER,
            golden_entities=golden,
            predicted_entities=predicted,
            difficulty_tier=DifficultyTier.EASY,
        )

        assert comp.true_positives == 0
        assert len(comp.missing_entities) == 1
        assert len(comp.hallucinated_entities) == 1

    def test_create_comparison_has_required_fields(self):
        engine = create_comparison_engine()
        golden = [{"id": "g1", "name": "Alice"}]
        predicted = [{"id": "g1", "name": "Alice", "confidence": 0.95}]

        comp = engine.create_comparison(
            extractor_type=EntityType.CHARACTER,
            golden_entities=golden,
            predicted_entities=predicted,
            difficulty_tier=DifficultyTier.EASY,
        )

        assert hasattr(comp, "matches")
        assert hasattr(comp, "matched_entities")
        assert hasattr(comp, "missing_entities")
        assert hasattr(comp, "hallucinated_entities")
        assert hasattr(comp, "duplicate_entities")
        assert hasattr(comp, "comparison_hash")
        assert hasattr(comp, "metadata")
        assert hasattr(comp, "true_positives")
        assert hasattr(comp, "false_positives")
        assert hasattr(comp, "false_negatives")
        assert hasattr(comp, "duplicates")

    def test_create_comparison_entity_match_result_uses_new_fields(self):
        engine = create_comparison_engine()
        golden = [{"id": "g1", "name": "Alice"}]
        predicted = [{"id": "g1", "name": "Alice", "confidence": 0.95}]

        comp = engine.create_comparison(
            extractor_type=EntityType.CHARACTER,
            golden_entities=golden,
            predicted_entities=predicted,
            difficulty_tier=DifficultyTier.EASY,
        )

        for mr in comp.matches:
            assert hasattr(mr, "similarity_score")
            assert hasattr(mr, "field_matches")
            assert not hasattr(mr, "confidence_score")
            assert not hasattr(mr, "field_scores")

            assert isinstance(mr.field_matches, dict)
            assert isinstance(mr.similarity_score, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

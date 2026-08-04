"""
Benchmark Scorer (RM-5.8.2)

Main scoring engine that orchestrates all metrics computation.
Completely offline, deterministic, no runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Any

from .models import (
    BenchmarkMetadata,
    BenchmarkResult,
    EntityType,
    DifficultyTier,
    MetricName,
    MetricScore,
    ExtractionComparison,
    ExtractorScore,
    OverallScore,
    Scorecard,
    Grade,
)
from .errors import BenchmarkError, MetricComputationError
from .metrics import (
    ExactMatchAccuracy,
    FieldLevelAccuracy,
    EntityLevelAccuracy,
    PrecisionMetric,
    RecallMetric,
    F1ScoreMetric,
    ConfidenceCalibrationMetric,
    SchemaComplianceMetric,
    BusinessRuleComplianceMetric,
    ReviewComplianceMetric,
)
from .metrics.accuracy import EntityMatcher


@dataclass
class ScorerConfig:
    """Configuration for benchmark scorer."""
    entity_matcher: Optional[EntityMatcher] = None
    enabled_metrics: List[MetricName] = field(default_factory=lambda: [
        MetricName.PRECISION,
        MetricName.RECALL,
        MetricName.F1_SCORE,
        MetricName.MISSING_RATE,
        MetricName.HALLUCINATION_RATE,
        MetricName.DUPLICATE_RATE,
        MetricName.SCHEMA_PASS_RATE,
        MetricName.BUSINESS_RULE_PASS_RATE,
        MetricName.REVIEW_PASS_RATE,
        MetricName.ECE,
        MetricName.FALSE_HIGH_CONFIDENCE,
        MetricName.FALSE_LOW_CONFIDENCE,
    ])
    difficulty_targets: Dict[DifficultyTier, Dict[MetricName, float]] = field(default_factory=lambda: {
        DifficultyTier.EASY: {
            MetricName.PRECISION: 0.85,
            MetricName.RECALL: 0.85,
            MetricName.F1_SCORE: 0.85,
            MetricName.MISSING_RATE: 0.15,
            MetricName.HALLUCINATION_RATE: 0.10,
            MetricName.DUPLICATE_RATE: 0.0,
            MetricName.SCHEMA_PASS_RATE: 1.0,
            MetricName.BUSINESS_RULE_PASS_RATE: 0.95,
            MetricName.REVIEW_PASS_RATE: 0.90,
            MetricName.ECE: 0.05,
            MetricName.FALSE_HIGH_CONFIDENCE: 0.05,
            MetricName.FALSE_LOW_CONFIDENCE: 0.10,
        },
        DifficultyTier.MEDIUM: {
            MetricName.PRECISION: 0.85,
            MetricName.RECALL: 0.75,
            MetricName.F1_SCORE: 0.75,
            MetricName.MISSING_RATE: 0.25,
            MetricName.HALLUCINATION_RATE: 0.15,
            MetricName.DUPLICATE_RATE: 0.0,
            MetricName.SCHEMA_PASS_RATE: 1.0,
            MetricName.BUSINESS_RULE_PASS_RATE: 0.95,
            MetricName.REVIEW_PASS_RATE: 0.90,
            MetricName.ECE: 0.05,
            MetricName.FALSE_HIGH_CONFIDENCE: 0.05,
            MetricName.FALSE_LOW_CONFIDENCE: 0.10,
        },
        DifficultyTier.HARD: {
            MetricName.PRECISION: 0.85,
            MetricName.RECALL: 0.65,
            MetricName.F1_SCORE: 0.65,
            MetricName.MISSING_RATE: 0.35,
            MetricName.HALLUCINATION_RATE: 0.20,
            MetricName.DUPLICATE_RATE: 0.0,
            MetricName.SCHEMA_PASS_RATE: 1.0,
            MetricName.BUSINESS_RULE_PASS_RATE: 0.95,
            MetricName.REVIEW_PASS_RATE: 0.90,
            MetricName.ECE: 0.05,
            MetricName.FALSE_HIGH_CONFIDENCE: 0.05,
            MetricName.FALSE_LOW_CONFIDENCE: 0.10,
        },
    })


class BenchmarkScorer:
    """Main benchmark scoring engine.
    
    Computes all metrics for a set of extraction comparisons against golden data.
    Deterministic, offline, no external dependencies.
    """
    
    def __init__(self, config: Optional[ScorerConfig] = None):
        self.config = config or ScorerConfig()
        self.matcher = self.config.entity_matcher or EntityMatcher()
        
        self.precision_metric = PrecisionMetric(self.matcher)
        self.recall_metric = RecallMetric(self.matcher)
        self.f1_metric = F1ScoreMetric(self.matcher)
        self.confidence_metric = ConfidenceCalibrationMetric(self.matcher)
        self.schema_metric = SchemaComplianceMetric()
        self.business_rule_metric = BusinessRuleComplianceMetric()
        self.review_metric = ReviewComplianceMetric()

    def generate_scorecard(
        self,
        comparisons: List[ExtractionComparison],
        metadata: BenchmarkMetadata,
    ) -> Scorecard:
        overall = OverallScore()
        extractor_groups: Dict[EntityType, List[ExtractionComparison]] = {}
        for c in comparisons:
            et = c.extractor_type
            extractor_groups.setdefault(et, []).append(c)

        for entity_type, comps in extractor_groups.items():
            extractor_score = ExtractorScore(extractor_type=entity_type)
            metrics_to_compute = [
                (self.precision_metric, MetricName.PRECISION),
                (self.recall_metric, MetricName.RECALL),
                (self.f1_metric, MetricName.F1_SCORE),
            ]
            for comp in comps:
                for metric_obj, metric_name in metrics_to_compute:
                    ms = metric_obj.compute(comp)
                    target = self._get_target(metric_name, comp.difficulty_tier)
                    scored = MetricScore(
                        metric_name=metric_name,
                        value=ms.value,
                        target=target,
                        passed=ms.value >= target,
                        difficulty_tier=comp.difficulty_tier,
                        details=ms.details,
                    )
                    extractor_score = extractor_score.add_metric(scored)

            extractor_score = replace(
                extractor_score,
                extractor_score=extractor_score.compute_weighted_score(),
            )
            overall = overall.add_extractor_score(extractor_score)

        overall = overall.compute_overall()
        return Scorecard(metadata=metadata, overall=overall)

    def _get_target(self, metric_name: MetricName, tier: DifficultyTier) -> float:
        tier_targets = self.config.difficulty_targets.get(tier, {})
        return tier_targets.get(metric_name, 0.85)


def create_scorer(config: Optional[ScorerConfig] = None) -> BenchmarkScorer:
    """Factory function to create a benchmark scorer."""
    return BenchmarkScorer(config)
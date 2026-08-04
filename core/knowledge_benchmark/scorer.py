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


def create_scorer(config: Optional[ScorerConfig] = None) -> BenchmarkScorer:
    """Factory function to create a benchmark scorer."""
    return BenchmarkScorer(config)
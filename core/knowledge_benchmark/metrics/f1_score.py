"""
F1 Score Metric (RM-5.8.2)

F1 Score metric for entity extraction evaluation.
F1 = 2 * (Precision * Recall) / (Precision + Recall)
"""

from __future__ import annotations

from typing import Optional

from ..models import (
    MetricName,
    MetricScore,
    EntityType,
    DifficultyTier,
    ExtractionComparison,
)
from .accuracy import EntityMatcher, MatchType
from .precision import PrecisionMetric, compute_precision
from .recall import RecallMetric, compute_recall


class F1ScoreMetric:
    """F1 Score metric for entity extraction.
    
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    Primary headline accuracy metric per RM-5.8.0.
    """
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
        self.precision_metric = PrecisionMetric(self.matcher)
        self.recall_metric = RecallMetric(self.matcher)
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute F1 score from comparison."""
        m = matcher or self.matcher
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        true_positives = sum(1 for match in matches if match.matched)
        false_positives = sum(1 for match in matches if not match.matched and match.predicted_entity_id)
        false_negatives = sum(1 for match in matches if not match.matched and match.golden_entity_id)
        
        precision = compute_precision(true_positives, false_positives)
        recall = compute_recall(true_positives, false_negatives)
        
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        
        # Target varies by difficulty tier per RM-5.8.0
        target_map = {
            DifficultyTier.EASY: 0.85,
            DifficultyTier.MEDIUM: 0.75,
            DifficultyTier.HARD: 0.65,
        }
        target = target_map.get(comparison.difficulty_tier, 0.85)
        
        return MetricScore(
            metric_name=MetricName.F1_SCORE,
            value=round(f1, 4),
            target=target,
            passed=f1 >= target,
            details={
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "precision": precision,
                "recall": recall,
                "matches": [mr.to_dict() for mr in matches],
            },
            difficulty_tier=comparison.difficulty_tier,
        )


def compute_f1(precision: float, recall: float) -> float:
    """Compute F1 score from precision and recall."""
    if precision + recall > 0:
        return round(2 * (precision * recall) / (precision + recall), 4)
    return 0.0
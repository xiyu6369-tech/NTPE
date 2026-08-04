"""
Precision Metric (RM-5.8.2)

Precision metric for entity extraction evaluation.
Precision = TP / (TP + FP)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..models import (
    MetricName,
    MetricScore,
    EntityType,
    DifficultyTier,
    ExtractionComparison,
)
from .accuracy import EntityMatcher, MatchType


class PrecisionMetric:
    """Precision metric for entity extraction.
    
    Precision = TP / (TP + FP)
    where TP = correctly extracted entities matching golden
    and FP = extracted entities not in golden
    """
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute precision from comparison."""
        m = matcher or self.matcher
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        # True positives: matched golden entities
        true_positives = sum(1 for match in matches if match.matched)
        
        # False positives: predicted entities not matched to any golden
        false_positives = sum(1 for match in matches if not match.matched and match.predicted_entity_id)
        
        total_predicted = true_positives + false_positives
        precision = true_positives / total_predicted if total_predicted > 0 else 1.0
        
        return MetricScore(
            metric_name=MetricName.PRECISION,
            value=round(precision, 4),
            target=0.85,  # Target from RM-5.8.0 for Easy tier
            passed=precision >= 0.85,
            details={
                "true_positives": true_positives,
                "false_positives": false_positives,
                "total_predicted": total_predicted,
                "matches": [mr.to_dict() for mr in matches],
            },
            difficulty_tier=comparison.difficulty_tier,
        )


def compute_precision(
    true_positives: int,
    false_positives: int,
) -> float:
    """Compute precision from counts."""
    total = true_positives + false_positives
    return round(true_positives / total, 4) if total > 0 else 1.0
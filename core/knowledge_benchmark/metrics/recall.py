"""
Recall Metric (RM-5.8.2)

Recall metric for entity extraction evaluation.
Recall = TP / (TP + FN)
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


class RecallMetric:
    """Recall metric for entity extraction.
    
    Recall = TP / (TP + FN)
    where TP = correctly extracted entities matching golden
    and FN = golden entities not extracted
    """
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute recall from comparison."""
        m = matcher or self.matcher
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        # True positives: matched golden entities
        true_positives = sum(1 for match in matches if match.matched)
        
        # False negatives: golden entities not matched
        false_negatives = sum(1 for match in matches if not match.matched and match.golden_entity_id)
        
        total_golden = true_positives + false_negatives
        recall = true_positives / total_golden if total_golden > 0 else 1.0
        
        return MetricScore(
            metric_name=MetricName.RECALL,
            value=round(recall, 4),
            target=0.85,  # Target from RM-5.8.0 for Easy tier
            passed=recall >= 0.85,
            details={
                "true_positives": true_positives,
                "false_negatives": false_negatives,
                "total_golden": total_golden,
                "matches": [mr.to_dict() for mr in matches],
            },
            difficulty_tier=comparison.difficulty_tier,
        )


def compute_recall(
    true_positives: int,
    false_negatives: int,
) -> float:
    """Compute recall from counts."""
    total = true_positives + false_negatives
    return round(true_positives / total, 4) if total > 0 else 1.0
"""
Confidence Metrics (RM-5.8.2)

Confidence calibration metrics for evaluating model confidence scores.
Includes ECE (Expected Calibration Error), False High Confidence Rate,
and False Low Confidence Rate per RM-5.8.0 METRICS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..models import (
    MetricName,
    MetricScore,
    EntityType,
    DifficultyTier,
    ExtractionComparison,
)
from .accuracy import EntityMatcher, MatchType


@dataclass
class ConfidenceBin:
    """Represents a confidence bin for ECE computation."""
    lower: float
    upper: float
    count: int = 0
    correct: int = 0
    total_confidence: float = 0.0
    
    @property
    def accuracy(self) -> float:
        return self.correct / self.count if self.count > 0 else 0.0
    
    @property
    def avg_confidence(self) -> float:
        return self.total_confidence / self.count if self.count > 0 else 0.0
class ExpectedCalibrationError:
    """Expected Calibration Error (ECE) computation.
    
    ECE = Σ (|accuracy(bin) - confidence(bin)| * |bin| / N)
    Uses 10 equal-width bins [0.0-0.1, 0.1-0.2, ..., 0.9-1.0]
    Target: ECE ≤ 0.05 per RM-5.8.0
    """
    
    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute ECE from comparison."""
        m = matcher or EntityMatcher()
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        bins = [ConfidenceBin(i/self.num_bins, (i+1)/self.num_bins) for i in range(self.num_bins)]
        
        for match in matches:
            if not match.predicted_entity_id:
                continue
            
            confidence = match.confidence_predicted
            is_correct = match.matched and match.match_type in (MatchType.EXACT.value, MatchType.FIELD_LEVEL.value)
            
            bin_idx = min(int(confidence * self.num_bins), self.num_bins - 1)
            bin_obj = bins[bin_idx]
            bin_obj.count += 1
            bin_obj.total_confidence += confidence
            if is_correct:
                bin_obj.correct += 1
        
        total_samples = sum(b.count for b in bins)
        if total_samples == 0:
            return MetricScore(
                metric_name=MetricName.ECE,
                value=0.0,
                target=0.05,
                passed=True,
                details={"bins": []},
                difficulty_tier=comparison.difficulty_tier,
            )
        
        ece = 0.0
        bin_details = []
        
        for bin_obj in bins:
            if bin_obj.count > 0:
                acc = bin_obj.accuracy
                conf = bin_obj.avg_confidence
                weight = bin_obj.count / total_samples
                ece += abs(acc - conf) * weight
                bin_details.append({
                    "lower": bin_obj.lower,
                    "upper": bin_obj.upper,
                    "count": bin_obj.count,
                    "accuracy": round(acc, 4),
                    "avg_confidence": round(conf, 4),
                    "weight": round(weight, 4),
                })
            else:
                bin_details.append({
                    "lower": bin_obj.lower,
                    "upper": bin_obj.upper,
                    "count": 0,
                    "accuracy": 0.0,
                    "avg_confidence": 0.0,
                    "weight": 0.0,
                })
        
        return MetricScore(
            metric_name=MetricName.ECE,
            value=round(ece, 4),
            target=0.05,
            passed=ece <= 0.05,
            details={
                "ece": round(ece, 4),
                "bins": bin_details,
                "total_samples": total_samples,
            },
            difficulty_tier=comparison.difficulty_tier,
        )
class FalseHighConfidenceRate:
    """False High Confidence Rate metric.
    
    False_High_Confidence = Count(confidence ≥ 0.8 AND incorrect) / Count(confidence ≥ 0.8)
    Target: ≤ 0.05 per RM-5.8.0
    """
    
    def __init__(self, high_confidence_threshold: float = 0.8):
        self.threshold = high_confidence_threshold
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute false high confidence rate."""
        m = matcher or EntityMatcher()
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        high_conf_count = 0
        false_high_count = 0
        
        for match in matches:
            if not match.predicted_entity_id:
                continue
            
            if match.confidence_predicted >= self.threshold:
                high_conf_count += 1
                is_correct = match.matched and match.match_type in (MatchType.EXACT.value, MatchType.FIELD_LEVEL.value)
                if not is_correct:
                    false_high_count += 1
        
        rate = false_high_count / high_conf_count if high_conf_count > 0 else 0.0
        
        return MetricScore(
            metric_name=MetricName.FALSE_HIGH_CONFIDENCE,
            value=round(rate, 4),
            target=0.05,
            passed=rate <= 0.05,
            details={
                "high_confidence_count": high_conf_count,
                "false_high_count": false_high_count,
                "threshold": self.threshold,
            },
            difficulty_tier=comparison.difficulty_tier,
        )


class FalseLowConfidenceRate:
    """False Low Confidence Rate metric.
    
    False_Low_Confidence = Count(confidence < 0.5 AND correct) / Count(confidence < 0.5)
    Target: ≤ 0.10 per RM-5.8.0
    """
    
    def __init__(self, low_confidence_threshold: float = 0.5):
        self.threshold = low_confidence_threshold
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute false low confidence rate."""
        m = matcher or EntityMatcher()
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        low_conf_count = 0
        false_low_count = 0
        
        for match in matches:
            if not match.predicted_entity_id:
                continue
            
            if match.confidence_predicted < self.threshold:
                low_conf_count += 1
                is_correct = match.matched and match.match_type in (MatchType.EXACT.value, MatchType.FIELD_LEVEL.value)
                if is_correct:
                    false_low_count += 1
        
        rate = false_low_count / low_conf_count if low_conf_count > 0 else 0.0
        
        return MetricScore(
            metric_name=MetricName.FALSE_LOW_CONFIDENCE,
            value=round(rate, 4),
            target=0.10,
            passed=rate <= 0.10,
            details={
                "low_confidence_count": low_conf_count,
                "false_low_count": false_low_count,
                "threshold": self.threshold,
            },
            difficulty_tier=comparison.difficulty_tier,
        )


class ConfidenceCalibrationMetric:
    """Combined confidence calibration metrics."""
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
        self.ece = ExpectedCalibrationError()
        self.false_high = FalseHighConfidenceRate()
        self.false_low = FalseLowConfidenceRate()
    
    def compute_all(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> Dict[MetricName, MetricScore]:
        """Compute all confidence metrics."""
        m = matcher or self.matcher
        return {
            MetricName.ECE: self.ece.compute(comparison, m),
            MetricName.FALSE_HIGH_CONFIDENCE: self.false_high.compute(comparison, m),
            MetricName.FALSE_LOW_CONFIDENCE: self.false_low.compute(comparison, m),
        }
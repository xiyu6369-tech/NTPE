"""
Accuracy Metrics (RM-5.8.2)

Accuracy metric implementations for entity extraction evaluation.
Supports exact match, field-level match, and entity-level comparison.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum

from ..models import (
    MetricName,
    MetricScore,
    EntityType,
    DifficultyTier,
    EntityMatchResult,
    ExtractionComparison,
)


class MatchType(str, Enum):
    """Types of entity matching."""
    EXACT = "exact"
    SEMANTIC = "semantic"
    FIELD_LEVEL = "field_level"
    NONE = "none"
@dataclass
class EntityMatcher:
    """Configurable entity matcher for comparing golden vs predicted entities."""
    
    key_fields: Dict[EntityType, List[str]] = field(default_factory=lambda: {
        EntityType.CHARACTER: ["name", "aliases"],
        EntityType.GLOSSARY: ["term", "translation"],
        EntityType.SCENE: ["location", "time_of_day"],
        EntityType.NARRATIVE: ["plot_point", "arc"],
        EntityType.STYLE: ["tone", "category"],
        EntityType.UNKNOWN: ["name"],
    })
    similarity_threshold: float = 0.85
    field_comparators: Dict[str, Callable[[Any, Any], bool]] = field(default_factory=dict)
    
    def match_entities(
        self,
        golden: List[Dict[str, Any]],
        predicted: List[Dict[str, Any]],
        extractor_type: EntityType,
    ) -> List[EntityMatchResult]:
        """Match golden entities to predicted entities."""
        results = []
        predicted_used: Set[int] = set()
        for g_entity in golden:
            best_match = None
            best_score = 0.0
            best_idx = -1
            
            for idx, p_entity in enumerate(predicted):
                if idx in predicted_used:
                    continue
                
                score, match_type = self._compute_similarity(g_entity, p_entity, extractor_type)
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = p_entity
                    best_idx = idx
                    best_match_type = match_type
            
            if best_match is not None:
                predicted_used.add(best_idx)
                field_matches = self._compare_fields(g_entity, best_match, extractor_type)
                results.append(EntityMatchResult(
                    golden_entity_id=g_entity.get("id", g_entity.get("entity_id", "")),
                    predicted_entity_id=best_match.get("id", best_match.get("entity_id", "")),
                    matched=True,
                    match_type=best_match_type,
                    similarity_score=best_score,
                    field_matches=field_matches,
                    confidence_golden=float(g_entity.get("confidence", 0.0)),
                    confidence_predicted=float(best_match.get("confidence", 0.0)),
                ))
            else:
                results.append(EntityMatchResult(
                    golden_entity_id=g_entity.get("id", g_entity.get("entity_id", "")),
                    predicted_entity_id=None,
                    matched=False,
                    match_type=MatchType.NONE.value,
                    similarity_score=0.0,
                    field_matches={},
                    confidence_golden=float(g_entity.get("confidence", 0.0)),
                    confidence_predicted=0.0,
                ))
        
        for idx, p_entity in enumerate(predicted):
            if idx not in predicted_used:
                results.append(EntityMatchResult(
                    golden_entity_id="",
                    predicted_entity_id=p_entity.get("id", p_entity.get("entity_id", "")),
                    matched=False,
                    match_type=MatchType.NONE.value,
                    similarity_score=0.0,
                    field_matches={},
                    confidence_golden=0.0,
                    confidence_predicted=float(p_entity.get("confidence", 0.0)),
                ))
        
        return results
    
    def _compute_similarity(
        self,
        golden: Dict[str, Any],
        predicted: Dict[str, Any],
        extractor_type: EntityType,
    ) -> tuple[float, str]:
        """Compute similarity between two entities."""
        g_id = golden.get("id", golden.get("entity_id", ""))
        p_id = predicted.get("id", predicted.get("entity_id", ""))
        if g_id and p_id and g_id == p_id:
            return 1.0, MatchType.EXACT.value
        
        key_fields = self.key_fields.get(extractor_type, ["name"])
        field_scores = []
        
        for field_name in key_fields:
            g_val = golden.get(field_name)
            p_val = predicted.get(field_name)
            
            if g_val is None or p_val is None:
                field_scores.append(0.0)
                continue
            
            if field_name in self.field_comparators:
                match = self.field_comparators[field_name](g_val, p_val)
                field_scores.append(1.0 if match else 0.0)
            elif isinstance(g_val, list) and isinstance(p_val, list):
                g_set = set(str(v) for v in g_val)
                p_set = set(str(v) for v in p_val)
                if g_set and p_set:
                    overlap = len(g_set & p_set) / len(g_set | p_set)
                    field_scores.append(overlap)
                else:
                    field_scores.append(0.0)
            elif isinstance(g_val, str) and isinstance(p_val, str):
                if g_val.lower() == p_val.lower():
                    field_scores.append(1.0)
                elif g_val.lower() in p_val.lower() or p_val.lower() in g_val.lower():
                    field_scores.append(0.8)
                else:
                    field_scores.append(0.0)
            else:
                field_scores.append(1.0 if g_val == p_val else 0.0)
        
        if field_scores:
            avg_score = sum(field_scores) / len(field_scores)
            if avg_score >= self.similarity_threshold:
                return avg_score, MatchType.FIELD_LEVEL.value
            elif avg_score > 0.5:
                return avg_score, MatchType.SEMANTIC.value
        
        return 0.0, MatchType.NONE.value
    
    def _compare_fields(
        self,
        golden: Dict[str, Any],
        predicted: Dict[str, Any],
        extractor_type: EntityType,
    ) -> Dict[str, bool]:
        """Compare individual fields between golden and predicted."""
        matches = {}
        key_fields = self.key_fields.get(extractor_type, ["name"])
        
        for field_name in key_fields:
            g_val = golden.get(field_name)
            p_val = predicted.get(field_name)
            
            if g_val is None and p_val is None:
                matches[field_name] = True
            elif g_val is None or p_val is None:
                matches[field_name] = False
            elif isinstance(g_val, list) and isinstance(p_val, list):
                matches[field_name] = set(str(v) for v in g_val) == set(str(v) for v in p_val)
            else:
                matches[field_name] = g_val == p_val
        
        return matches


class AccuracyMetric(ABC):
    """Abstract base class for accuracy metrics."""
    
    @abstractmethod
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute accuracy metric from comparison."""
        pass


class ExactMatchAccuracy(AccuracyMetric):
    """Exact match accuracy - entities must match exactly by ID."""
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute exact match accuracy."""
        if not comparison.golden_entities:
            return MetricScore(
                metric_name=MetricName.F1_SCORE,
                value=1.0 if not comparison.predicted_entities else 0.0,
                target=1.0,
                passed=not comparison.predicted_entities,
                details={"method": "exact_match"},
            )
        
        golden_ids = {e.get("id", e.get("entity_id", "")) for e in comparison.golden_entities}
        predicted_ids = {e.get("id", e.get("entity_id", "")) for e in comparison.predicted_entities}
        
        exact_matches = len(golden_ids & predicted_ids)
        total_golden = len(golden_ids)
        
        accuracy = exact_matches / total_golden if total_golden > 0 else 0.0
        
        return MetricScore(
            metric_name=MetricName.F1_SCORE,
            value=round(accuracy, 4),
            target=1.0,
            passed=accuracy >= 1.0,
            details={
                "method": "exact_match",
                "exact_matches": exact_matches,
                "total_golden": total_golden,
                "total_predicted": len(predicted_ids),
            },
            difficulty_tier=comparison.difficulty_tier,
        )


class FieldLevelAccuracy(AccuracyMetric):
    """Field-level accuracy - compare key fields of entities."""
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute field-level accuracy."""
        m = matcher or self.matcher
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        field_level_matches = sum(
            1 for m in matches 
            if m.matched and m.match_type in (MatchType.EXACT.value, MatchType.FIELD_LEVEL.value)
        )
        total_golden = len(comparison.golden_entities)
        
        accuracy = field_level_matches / total_golden if total_golden > 0 else 0.0
        
        return MetricScore(
            metric_name=MetricName.F1_SCORE,
            value=round(accuracy, 4),
            target=0.85,
            passed=accuracy >= 0.85,
            details={
                "method": "field_level",
                "field_level_matches": field_level_matches,
                "total_golden": total_golden,
                "total_predicted": len(comparison.predicted_entities),
                "matches": [mr.to_dict() for mr in matches],
            },
            difficulty_tier=comparison.difficulty_tier,
        )


class EntityLevelAccuracy(AccuracyMetric):
    """Entity-level accuracy - semantic matching of entities."""
    
    def __init__(self, matcher: Optional[EntityMatcher] = None):
        self.matcher = matcher or EntityMatcher()
    
    def compute(
        self,
        comparison: ExtractionComparison,
        matcher: Optional[EntityMatcher] = None,
    ) -> MetricScore:
        """Compute entity-level accuracy with semantic matching."""
        m = matcher or self.matcher
        matches = m.match_entities(
            comparison.golden_entities,
            comparison.predicted_entities,
            comparison.extractor_type,
        )
        
        matched_count = sum(1 for m in matches if m.matched)
        total_golden = len(comparison.golden_entities)
        
        accuracy = matched_count / total_golden if total_golden > 0 else 0.0
        
        return MetricScore(
            metric_name=MetricName.F1_SCORE,
            value=round(accuracy, 4),
            target=0.75,
            passed=accuracy >= 0.75,
            details={
                "method": "entity_level",
                "matched_entities": matched_count,
                "total_golden": total_golden,
                "total_predicted": len(comparison.predicted_entities),
                "matches": [mr.to_dict() for mr in matches],
            },
            difficulty_tier=comparison.difficulty_tier,
        )

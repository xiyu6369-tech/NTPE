"""
Comparison Engine (RM-5.8.2)

Golden vs prediction comparison and regression detection.
Completely offline, deterministic, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import hashlib
import json
from datetime import datetime

from .models import (
    BenchmarkMetadata,
    EntityType,
    DifficultyTier,
    MetricName,
    ExtractionComparison,
    EntityMatchResult,
    
    Scorecard,
)
from .errors import ComparisonError, GoldenDatasetError
from .metrics.accuracy import EntityMatcher, MatchType
from .scorer import BenchmarkScorer, ScorerConfig


class RegressionType(Enum):
    """Types of regression detected."""
    F1_DROP = "f1_drop"
    PRECISION_DROP = "precision_drop"
    RECALL_DROP = "recall_drop"
    SCHEMA_REGRESSION = "schema_regression"
    BUSINESS_RULE_REGRESSION = "business_rule_regression"
    CONFIDENCE_REGRESSION = "confidence_regression"


@dataclass
class RegressionResult:
    """Result of regression detection."""
    regression_type: RegressionType
    extractor_type: EntityType
    difficulty_tier: DifficultyTier
    previous_value: float
    current_value: float
    delta: float
    threshold: float
    is_regression: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonConfig:
    """Configuration for comparison engine."""
    entity_matcher: Optional[EntityMatcher] = None
    regression_thresholds: Dict[RegressionType, float] = field(default_factory=lambda: {
        RegressionType.F1_DROP: 0.02,
        RegressionType.PRECISION_DROP: 0.02,
        RegressionType.RECALL_DROP: 0.02,
        RegressionType.SCHEMA_REGRESSION: 0.0,
        RegressionType.BUSINESS_RULE_REGRESSION: 0.05,
        RegressionType.CONFIDENCE_REGRESSION: 0.02,
    })
    enable_regression_detection: bool = True
    cache_comparisons: bool = True


class ComparisonEngine:
    """Engine for comparing golden data with predictions.
    
    Supports:
    - Single comparison (golden vs prediction)
    - Batch comparison across multiple extractors/tiers
    - Regression detection against previous benchmarks
    - Deterministic comparison hashing for reproducibility
    """
    
    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig()
        self.matcher = self.config.entity_matcher or EntityMatcher()
        self.scorer = BenchmarkScorer(ScorerConfig(entity_matcher=self.matcher))
        self._comparison_cache: Dict[str, ExtractionComparison] = {}
        self._previous_scorecards: List[Scorecard] = []
    
    def create_comparison(
        self,
        extractor_type: EntityType,
        golden_entities: List[Dict[str, Any]],
        predicted_entities: List[Dict[str, Any]],
        difficulty_tier: DifficultyTier,
        source_text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExtractionComparison:
        """Create an extraction comparison with entity matching."""
        matches = self.matcher.match_entities(
            golden_entities,
            predicted_entities,
            extractor_type,
        )
        
        matched_golden_ids = set()
        matched_predicted_ids = set()
        
        for mr in matches:
            if mr.matched:
                matched_golden_ids.add(mr.golden_entity_id)
                if mr.predicted_entity_id:
                    matched_predicted_ids.add(mr.predicted_entity_id)
        
        missing_entities = []
        for entity in golden_entities:
            eid = entity.get("id", entity.get("entity_id", ""))
            if eid not in matched_golden_ids:
                missing_entities.append(entity)
        
        hallucinated_entities = []
        for entity in predicted_entities:
            eid = entity.get("id", entity.get("entity_id", ""))
            if eid not in matched_predicted_ids:
                hallucinated_entities.append(entity)
        
        duplicate_entities = []
        pred_ids = [e.get("id", e.get("entity_id", "")) for e in predicted_entities]
        id_counts: Dict[str, int] = {}
        for pid in pred_ids:
            id_counts[pid] = id_counts.get(pid, 0) + 1
        for pid, count in id_counts.items():
            if count > 1:
                for entity in predicted_entities:
                    if entity.get("id", entity.get("entity_id", "")) == pid:
                        duplicate_entities.append(entity)
                        break
        
        comparison_hash = self._generate_comparison_hash(
            extractor_type, difficulty_tier, golden_entities, predicted_entities
        )
        
        matched_count = len(matched_golden_ids)
        
        return ExtractionComparison(
            extractor_type=extractor_type,
            difficulty_tier=difficulty_tier,
            golden_entities=golden_entities,
            predicted_entities=predicted_entities,
            matches=matches,
            matched_entities=list(matches),
            true_positives=matched_count,
            false_positives=len(predicted_entities) - matched_count,
            false_negatives=len(golden_entities) - matched_count,
            duplicates=len(duplicate_entities),
            missing_entities=missing_entities,
            hallucinated_entities=hallucinated_entities,
            duplicate_entities=duplicate_entities,
            comparison_hash=comparison_hash,
            metadata=metadata or {},
        )
    
    def _generate_comparison_hash(
        self,
        extractor_type: EntityType,
        difficulty_tier: DifficultyTier,
        golden_entities: List[Dict[str, Any]],
        predicted_entities: List[Dict[str, Any]],
    ) -> str:
        """Generate deterministic SHA256 hash for comparison reproducibility."""
        content = {
            "extractor": extractor_type.value,
            "difficulty": difficulty_tier.value,
            "golden": sorted([
                {k: v for k, v in e.items() if k != "confidence"}
                for e in golden_entities
            ], key=lambda x: x.get("id", x.get("entity_id", ""))),
            "predicted": sorted([
                {k: v for k, v in e.items() if k != "confidence"}
                for e in predicted_entities
            ], key=lambda x: x.get("id", x.get("entity_id", ""))),
        }
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode("utf-8")).hexdigest()[:16]
    
    def compare_batch(
        self,
        comparisons: List[Tuple[EntityType, List[Dict[str, Any]], List[Dict[str, Any]], DifficultyTier, str, Optional[Dict[str, Any]]]],
    ) -> List[ExtractionComparison]:
        """Create multiple comparisons in batch."""
        results = []
        for extractor_type, golden, predicted, difficulty, source_text, metadata in comparisons:
            comparison = self.create_comparison(
                extractor_type, golden, predicted, difficulty, source_text, metadata
            )
            results.append(comparison)
        return results
    
    def score_comparison(
        self,
        comparison: ExtractionComparison,
        metadata: Optional[BenchmarkMetadata] = None,
    ) -> List:
        """Score a single comparison using the benchmark scorer."""
        return self.scorer.score_comparison(comparison, metadata)
    
    def score_batch(
        self,
        comparisons: List[ExtractionComparison],
        metadata: Optional[BenchmarkMetadata] = None,
    ) -> Dict[EntityType, Dict[DifficultyTier, List]]:
        """Score multiple comparisons."""
        return self.scorer.score_multiple_comparisons(comparisons, metadata)
    
    def generate_scorecard(
        self,
        comparisons: List[ExtractionComparison],
        metadata: BenchmarkMetadata,
    ) -> Scorecard:
        """Generate a scorecard from comparisons."""
        scorecard = self.scorer.generate_scorecard(comparisons, metadata)
        
        if self.config.cache_comparisons:
            self._previous_scorecards.append(scorecard)
        
        return scorecard
    def detect_regression(
        self,
        current_scorecard: Scorecard,
        baseline_scorecard: Optional[Scorecard] = None,
    ) -> List[RegressionResult]:
        """Detect regressions by comparing current scorecard against baseline."""
        regressions = []
        
        if baseline_scorecard is None:
            if not self._previous_scorecards:
                return regressions
            baseline_scorecard = self._previous_scorecards[-1]
        
        if not self.config.enable_regression_detection:
            return regressions
        
        for extractor_type, current_es in current_scorecard.overall.extractor_scores.items():
            if extractor_type not in baseline_scorecard.overall.extractor_scores:
                continue
            
            baseline_es = baseline_scorecard.overall.extractor_scores[extractor_type]
            
            self._check_metric_regression(
                regressions,
                RegressionType.F1_DROP,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.F1_SCORE,
            )
            
            self._check_metric_regression(
                regressions,
                RegressionType.PRECISION_DROP,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.PRECISION,
            )
            
            self._check_metric_regression(
                regressions,
                RegressionType.RECALL_DROP,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.RECALL,
            )
            
            self._check_metric_regression(
                regressions,
                RegressionType.SCHEMA_REGRESSION,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.SCHEMA_PASS_RATE,
            )
            
            self._check_metric_regression(
                regressions,
                RegressionType.BUSINESS_RULE_REGRESSION,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.BUSINESS_RULE_PASS_RATE,
            )
            
            self._check_metric_regression(
                regressions,
                RegressionType.CONFIDENCE_REGRESSION,
                extractor_type,
                current_es,
                baseline_es,
                MetricName.ECE,
            )
        
        return regressions
    
    def _check_metric_regression(
        self,
        regressions: List[RegressionResult],
        regression_type: RegressionType,
        extractor_type: EntityType,
        current_es,
        baseline_es,
        metric_name: MetricName,
    ) -> None:
        """Check a specific metric for regression."""
        threshold = self.config.regression_thresholds.get(regression_type, 0.02)
        
        current_metric = current_es.metric_scores.get(metric_name)
        baseline_metric = baseline_es.metric_scores.get(metric_name)
        
        if current_metric is None or baseline_metric is None:
            return
        
        current_value = current_metric.value
        baseline_value = baseline_metric.value
        delta = baseline_value - current_value
        
        is_inverted = metric_name in (MetricName.MISSING_RATE, MetricName.HALLUCINATION_RATE,
                                      MetricName.DUPLICATE_RATE, MetricName.ECE,
                                      MetricName.FALSE_HIGH_CONFIDENCE, MetricName.FALSE_LOW_CONFIDENCE)
        
        if is_inverted:
            delta = current_value - baseline_value
        
        is_regression = delta > threshold
        
        if is_regression:
            regressions.append(RegressionResult(
                regression_type=regression_type,
                extractor_type=extractor_type,
                difficulty_tier=DifficultyTier.EASY,
                previous_value=baseline_value,
                current_value=current_value,
                delta=round(delta, 4),
                threshold=threshold,
                is_regression=True,
                details={
                    "metric": metric_name.value,
                    "extractor": extractor_type.value,
                }
            ))
    
    def get_comparison_hash(self, comparison: ExtractionComparison) -> str:
        """Get the deterministic hash for a comparison."""
        return comparison.comparison_hash
    
    def verify_determinism(
        self,
        comparison: ExtractionComparison,
    ) -> bool:
        """Verify that a comparison produces the same hash when recreated."""
        new_hash = self._generate_comparison_hash(
            comparison.extractor_type,
            comparison.difficulty_tier,
            comparison.golden_entities,
            comparison.predicted_entities,
        )
        return new_hash == comparison.comparison_hash
    
    def load_golden_dataset(
        self,
        path: str,
    ) -> Dict[EntityType, Dict[DifficultyTier, List[Dict[str, Any]]]]:
        """Load golden dataset from JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise GoldenDatasetError(f"Failed to load golden dataset from {path}: {e}")
        
        result = {}
        for entity_type_str, tier_data in data.items():
            try:
                entity_type = EntityType(entity_type_str.upper())
            except ValueError:
                raise GoldenDatasetError(f"Unknown entity type: {entity_type_str}")
            
            result[entity_type] = {}
            for tier_str, entities in tier_data.items():
                try:
                    difficulty = DifficultyTier(tier_str.upper())
                except ValueError:
                    raise GoldenDatasetError(f"Unknown difficulty tier: {tier_str}")
                result[entity_type][difficulty] = entities
        
        return result
    
    def save_comparison(
        self,
        comparison: ExtractionComparison,
        path: str,
    ) -> None:
        """Save comparison to JSON file for reproducibility."""
        data = {
            "extractor_type": comparison.extractor_type.value,
            "difficulty_tier": comparison.difficulty_tier.value,
            "golden_entities": comparison.golden_entities,
            "predicted_entities": comparison.predicted_entities,
            "matched_entities": [
                {
                    "golden_entity_id": m.golden_entity_id,
                    "predicted_entity_id": m.predicted_entity_id,
                    "match_type": m.match_type.value if hasattr(m.match_type, 'value') else m.match_type,
                    "similarity_score": m.similarity_score,
                    "field_matches": m.field_matches,
                }
                for m in comparison.matched_entities
            ],
            "missing_entities": comparison.missing_entities,
            "hallucinated_entities": comparison.hallucinated_entities,
            "duplicate_entities": comparison.duplicate_entities,
            "comparison_hash": comparison.comparison_hash,
            "metadata": comparison.metadata,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_comparison(
        self,
        path: str,
    ) -> ExtractionComparison:
        """Load comparison from JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ComparisonError(f"Failed to load comparison from {path}: {e}")
        
        matched_entities = [
            EntityMatchResult(
                golden_entity_id=m["golden_entity_id"],
                predicted_entity_id=m["predicted_entity_id"],
                matched=True,
                match_type=m["match_type"],
                similarity_score=m.get("similarity_score", m.get("confidence_score", 0.0)),
                field_matches=m.get("field_matches", m.get("field_scores", {})),
            )
            for m in data.get("matched_entities", [])
        ]
        
        return ExtractionComparison(
            extractor_type=EntityType(data["extractor_type"]),
            difficulty_tier=DifficultyTier(data["difficulty_tier"]),
            golden_entities=data["golden_entities"],
            predicted_entities=data["predicted_entities"],
            matched_entities=matched_entities,
            missing_entities=data["missing_entities"],
            hallucinated_entities=data["hallucinated_entities"],
            duplicate_entities=data["duplicate_entities"],
            comparison_hash=data["comparison_hash"],
            metadata=data.get("metadata", {}),
        )


def create_comparison_engine(config: Optional[ComparisonConfig] = None) -> ComparisonEngine:
    """Factory function to create a comparison engine."""
    return ComparisonEngine(config)
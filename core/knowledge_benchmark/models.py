"""
Benchmark Result Models (RM-5.8.2)

Standardized data models for benchmark results, metrics, and scorecards.
All models are deterministic and immutable where appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
import hashlib
import json


def utc_now_iso() -> str:
    """Return a stable UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def compute_hash(obj: Any) -> str:
    """Compute deterministic SHA256 hash of a JSON-serializable object."""
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


class EntityType(str, Enum):
    """Enumeration of knowledge entity types."""
    CHARACTER = "character"
    GLOSSARY = "glossary"
    SCENE = "scene"
    NARRATIVE = "narrative"
    STYLE = "style"
    UNKNOWN = "unknown"


class MetricName(str, Enum):
    """Standardized metric names per RM-5.8.0 METRICS."""
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    MISSING_RATE = "missing_rate"
    HALLUCINATION_RATE = "hallucination_rate"
    DUPLICATE_RATE = "duplicate_rate"
    SCHEMA_PASS_RATE = "schema_pass_rate"
    BUSINESS_RULE_PASS_RATE = "business_rule_pass_rate"
    REVIEW_PASS_RATE = "review_pass_rate"
    ECE = "ece"
    FALSE_HIGH_CONFIDENCE = "false_high_confidence"
    FALSE_LOW_CONFIDENCE = "false_low_confidence"
    COMPILATION_SUCCESS = "compilation_success"
    PACKAGE_VERIFICATION = "package_verification"
    DETERMINISTIC_REBUILD = "deterministic_rebuild"


class DifficultyTier(str, Enum):
    """Difficulty tiers for benchmark entries."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Grade(str, Enum):
    """Scorecard grades per RM-5.8.0 SCORECARD."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    F = "F"
@dataclass(frozen=True)
class BenchmarkMetadata:
    """Immutable metadata for a benchmark run."""
    benchmark_id: str
    benchmark_version: str = "RM-5.8.2"
    golden_dataset_version: str = "v1.0.0"
    config_hash: str = ""
    runtime_version: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    environment: str = "offline"
    deterministic_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "golden_dataset_version": self.golden_dataset_version,
            "config_hash": self.config_hash,
            "runtime_version": self.runtime_version,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "deterministic_seed": self.deterministic_seed,
        }

    @classmethod
    def create(
        cls,
        golden_dataset_version: str,
        config_hash: str,
        runtime_version: str,
        deterministic_seed: int = 42,
    ) -> "BenchmarkMetadata":
        """Create new benchmark metadata with generated ID."""
        benchmark_id = f"bench_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        return cls(
            benchmark_id=benchmark_id,
            golden_dataset_version=golden_dataset_version,
            config_hash=config_hash,
            runtime_version=runtime_version,
            deterministic_seed=deterministic_seed,
        )


@dataclass(frozen=True)
class MetricScore:
    """Immutable metric score with value, target, and pass/fail status."""
    metric_name: MetricName
    value: float
    target: float
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    difficulty_tier: Optional[DifficultyTier] = None

    def __post_init__(self):
        # Ensure 4 decimal places precision per RM-5.8.0
        object.__setattr__(self, "value", round(float(self.value), 4))
        object.__setattr__(self, "target", round(float(self.target), 4))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name.value,
            "value": self.value,
            "target": self.target,
            "passed": self.passed,
            "details": dict(self.details),
            "difficulty_tier": self.difficulty_tier.value if self.difficulty_tier else None,
        }


@dataclass(frozen=True)
class EntityMatchResult:
    """Result of matching a golden entity to a predicted entity."""
    golden_entity_id: str
    predicted_entity_id: Optional[str]
    matched: bool
    match_type: str
    similarity_score: float = 0.0
    field_matches: Dict[str, bool] = field(default_factory=dict)
    confidence_golden: float = 0.0
    confidence_predicted: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "golden_entity_id": self.golden_entity_id,
            "predicted_entity_id": self.predicted_entity_id,
            "matched": self.matched,
            "match_type": self.match_type,
            "similarity_score": round(self.similarity_score, 4),
            "field_matches": dict(self.field_matches),
            "confidence_golden": round(self.confidence_golden, 4),
            "confidence_predicted": round(self.confidence_predicted, 4),
        }


@dataclass(frozen=True)
class ExtractionComparison:
    """Comparison between golden and predicted extractions for one entry."""
    entry_id: str = ""
    extractor_type: EntityType = EntityType.UNKNOWN
    difficulty_tier: DifficultyTier = DifficultyTier.EASY
    golden_entities: List[Dict[str, Any]] = field(default_factory=list)
    predicted_entities: List[Dict[str, Any]] = field(default_factory=list)
    matches: List[EntityMatchResult] = field(default_factory=list)
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    duplicates: int = 0
    matched_entities: List[EntityMatchResult] = field(default_factory=list)
    missing_entities: List[Dict[str, Any]] = field(default_factory=list)
    hallucinated_entities: List[Dict[str, Any]] = field(default_factory=list)
    duplicate_entities: List[Dict[str, Any]] = field(default_factory=list)
    comparison_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "extractor_type": self.extractor_type.value,
            "difficulty_tier": self.difficulty_tier.value,
            "golden_entities": [e for e in self.golden_entities],
            "predicted_entities": [e for e in self.predicted_entities],
            "matches": [m.to_dict() for m in self.matches],
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "duplicates": self.duplicates,
        }

@dataclass
class BenchmarkResult:
    """Complete benchmark result for a single extractor run."""
    benchmark_id: str
    extractor_type: EntityType
    metric_name: MetricName
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Optional[BenchmarkMetadata] = None
    difficulty_tier: Optional[DifficultyTier] = None
    comparison: Optional[ExtractionComparison] = None

    def __post_init__(self):
        # Ensure deterministic score rounding
        self.score = round(float(self.score), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "extractor_type": self.extractor_type.value,
            "metric_name": self.metric_name.value,
            "score": self.score,
            "details": dict(self.details),
            "timestamp": self.timestamp,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "difficulty_tier": self.difficulty_tier.value if self.difficulty_tier else None,
            "comparison": self.comparison.to_dict() if self.comparison else None,
        }

    def with_metadata(self, metadata: BenchmarkMetadata) -> "BenchmarkResult":
        """Return new result with metadata (immutable pattern)."""
        return replace(self, metadata=metadata)

    @classmethod
    def create(
        cls,
        benchmark_id: str,
        extractor_type: EntityType,
        metric_name: MetricName,
        score: float,
        details: Optional[Dict[str, Any]] = None,
        difficulty_tier: Optional[DifficultyTier] = None,
        comparison: Optional[ExtractionComparison] = None,
    ) -> "BenchmarkResult":
        """Factory method for creating benchmark result."""
        return cls(
            benchmark_id=benchmark_id,
            extractor_type=extractor_type,
            metric_name=metric_name,
            score=round(float(score), 4),
            details=details or {},
            difficulty_tier=difficulty_tier,
            comparison=comparison,
        )


@dataclass(frozen=True)
class ExtractorScore:
    """Aggregated score for a single extractor per RM-5.8.0 METRICS aggregation."""
    extractor_type: EntityType
    metric_scores: Dict[MetricName, MetricScore] = field(default_factory=dict)
    extractor_score: float = 0.0

    def add_metric(self, metric: MetricScore) -> "ExtractorScore":
        """Return new ExtractorScore with added metric (immutable)."""
        new_metrics = dict(self.metric_scores)
        new_metrics[metric.metric_name] = metric
        return replace(self, metric_scores=new_metrics)

    def compute_weighted_score(self) -> float:
        """Compute weighted extractor score per RM-5.8.0 formula."""
        weights = {
            MetricName.F1_SCORE: 0.40,
            MetricName.MISSING_RATE: 0.15,
            MetricName.HALLUCINATION_RATE: 0.15,
            MetricName.SCHEMA_PASS_RATE: 0.10,
            MetricName.BUSINESS_RULE_PASS_RATE: 0.10,
            MetricName.ECE: 0.10,
        }

        total = 0.0
        for metric_name, weight in weights.items():
            if metric_name in self.metric_scores:
                metric = self.metric_scores[metric_name]
                if metric_name in (MetricName.MISSING_RATE, MetricName.HALLUCINATION_RATE, MetricName.ECE):
                    total += (1.0 - metric.value) * weight
                else:
                    total += metric.value * weight
        return round(total, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type.value,
            "metric_scores": {k.value: v.to_dict() for k, v in self.metric_scores.items()},
            "extractor_score": self.extractor_score,
        }


@dataclass(frozen=True)
class OverallScore:
    """Overall benchmark score across all extractors."""
    extractor_scores: Dict[EntityType, ExtractorScore] = field(default_factory=dict)
    overall_score: float = 0.0
    grade: Grade = Grade.F

    def add_extractor_score(self, score: ExtractorScore) -> "OverallScore":
        """Return new OverallScore with added extractor score (immutable)."""
        new_scores = dict(self.extractor_scores)
        new_scores[score.extractor_type] = score
        return replace(self, extractor_scores=new_scores)

    def compute_overall(self) -> "OverallScore":
        """Compute overall score as mean of extractor scores."""
        if not self.extractor_scores:
            return replace(self, overall_score=0.0, grade=Grade.F)

        total = sum(es.extractor_score for es in self.extractor_scores.values())
        overall = round(total / len(self.extractor_scores), 4)

        if overall >= 0.95:
            grade = Grade.A_PLUS
        elif overall >= 0.90:
            grade = Grade.A
        elif overall >= 0.80:
            grade = Grade.B
        elif overall >= 0.70:
            grade = Grade.C
        else:
            grade = Grade.F

        return replace(self, overall_score=overall, grade=grade)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_scores": {k.value: v.to_dict() for k, v in self.extractor_scores.items()},
            "overall_score": self.overall_score,
            "grade": self.grade.value,
        }
@dataclass(frozen=True)
class Scorecard:
    """Complete benchmark scorecard per RM-5.8.0 SCORECARD specification."""
    metadata: BenchmarkMetadata
    overall: OverallScore
    regression_check: Optional[Dict[str, Any]] = None
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Generate markdown scorecard per RM-5.8.0 SCORECARD format."""
        lines = [
            "# Knowledge Benchmark Scorecard",
            "",
            f"**Run ID**: `{self.metadata.benchmark_id}`",
            f"**Timestamp**: `{self.metadata.timestamp}`",
            f"**Golden Dataset Version**: `{self.metadata.golden_dataset_version}`",
            f"**Benchmark Version**: `{self.metadata.benchmark_version}`",
            f"**Configuration**: `{self.metadata.config_hash}`",
            "",
            "---",
            "",
            "## Extractor Scores",
            "",
        ]

        for extractor_type in EntityType:
            if extractor_type == EntityType.UNKNOWN:
                continue
            if extractor_type not in self.overall.extractor_scores:
                continue

            es = self.overall.extractor_scores[extractor_type]
            lines.append(f"### {extractor_type.value.capitalize()}")
            lines.append("| Metric | Value | Target | Status |")
            lines.append("|--------|-------|--------|--------|")

            for metric_name in MetricName:
                if metric_name not in es.metric_scores:
                    continue
                ms = es.metric_scores[metric_name]
                status = "✅ PASS" if ms.passed else "❌ FAIL"
                tier_str = f" ({ms.difficulty_tier.value})" if ms.difficulty_tier else ""
                lines.append(
                    f"| {metric_name.value}{tier_str} | {ms.value:.4f} | {ms.target:.4f} | {status} |"
                )

            lines.append(f"| **Extractor Score** | **{es.extractor_score:.4f}** | — | — |")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## Overall Score",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ])

        for extractor_type in EntityType:
            if extractor_type == EntityType.UNKNOWN:
                continue
            if extractor_type in self.overall.extractor_scores:
                es = self.overall.extractor_scores[extractor_type]
                lines.append(f"| {extractor_type.value.capitalize()} | {es.extractor_score:.4f} |")

        lines.append(f"| **Overall Score** | **{self.overall.overall_score:.4f} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Grade")
        lines.append("")
        lines.append("| Overall Score | Grade |")
        lines.append("|---------------|-------|")
        lines.append(f"| {self.overall.overall_score:.4f} | **{self.overall.grade.value}** |")
        lines.append("")

        if self.regression_check:
            lines.extend([
                "---",
                "",
                "## Regression Check",
                "",
                "| Extractor | Baseline F1 | Current F1 | Delta | Status |",
                "|-----------|-------------|------------|-------|--------|",
            ])
            for rc in self.regression_check.get("details", []):
                status = "✅ PASS" if rc["status"] == "pass" else "❌ FAIL"
                lines.append(
                    f"| {rc['extractor']} | {rc['baseline_f1']:.4f} | {rc['current_f1']:.4f} | {rc['delta']:+.4f} | {status} |"
                )
            lines.append("")
            lines.append(f"**Regression Threshold**: F1 drop > 0.02 (2 percentage points)")
            lines.append(f"**Result**: {self.regression_check.get('result', 'UNKNOWN')}")
            lines.append("")

        if self.summary:
            lines.extend([
                "---",
                "",
                "## Summary",
                "",
            ])
            for key, value in self.summary.items():
                lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "overall": self.overall.to_dict(),
            "regression_check": self.regression_check,
            "summary": dict(self.summary),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

"""
Analysis Models (RM-5.8.4)

Data models for the Knowledge Benchmark Analysis Engine.
All models are offline-compatible and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_hash(obj: Any) -> str:
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


class FailureCategory(str, Enum):
    MISSING_ENTITY = "MISSING_ENTITY"
    HALLUCINATION = "HALLUCINATION"
    WRONG_ALIAS = "WRONG_ALIAS"
    WRONG_RELATIONSHIP = "WRONG_RELATIONSHIP"
    WRONG_SCENE_BOUNDARY = "WRONG_SCENE_BOUNDARY"
    WRONG_TIMELINE = "WRONG_TIMELINE"
    WRONG_STYLE = "WRONG_STYLE"
    WRONG_GLOSSARY = "WRONG_GLOSSARY"
    DUPLICATE = "DUPLICATE"
    OVER_MERGE = "OVER_MERGE"
    UNDER_MERGE = "UNDER_MERGE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    BUSINESS_RULE_FAILURE = "BUSINESS_RULE_FAILURE"

    @classmethod
    def from_extractor(cls, extractor_type: str, match_type: str) -> "FailureCategory":
        rules = {
            "character": {
                "missing_entity": cls.MISSING_ENTITY,
                "hallucination": cls.HALLUCINATION,
                "wrong_alias": cls.WRONG_ALIAS,
                "wrong_relationship": cls.WRONG_RELATIONSHIP,
                "duplicate": cls.DUPLICATE,
                "over_merge": cls.OVER_MERGE,
                "under_merge": cls.UNDER_MERGE,
                "low_confidence": cls.LOW_CONFIDENCE,
                "schema_failure": cls.SCHEMA_FAILURE,
                "business_rule_failure": cls.BUSINESS_RULE_FAILURE,
            },
            "glossary": {
                "missing_entity": cls.MISSING_ENTITY,
                "hallucination": cls.HALLUCINATION,
                "wrong_glossary": cls.WRONG_GLOSSARY,
                "duplicate": cls.DUPLICATE,
                "over_merge": cls.OVER_MERGE,
                "under_merge": cls.UNDER_MERGE,
                "low_confidence": cls.LOW_CONFIDENCE,
                "schema_failure": cls.SCHEMA_FAILURE,
                "business_rule_failure": cls.BUSINESS_RULE_FAILURE,
            },
            "scene": {
                "missing_entity": cls.MISSING_ENTITY,
                "hallucination": cls.HALLUCINATION,
                "wrong_scene_boundary": cls.WRONG_SCENE_BOUNDARY,
                "duplicate": cls.DUPLICATE,
                "over_merge": cls.OVER_MERGE,
                "under_merge": cls.UNDER_MERGE,
                "low_confidence": cls.LOW_CONFIDENCE,
                "schema_failure": cls.SCHEMA_FAILURE,
                "business_rule_failure": cls.BUSINESS_RULE_FAILURE,
            },
            "narrative": {
                "missing_entity": cls.MISSING_ENTITY,
                "hallucination": cls.HALLUCINATION,
                "wrong_timeline": cls.WRONG_TIMELINE,
                "wrong_relationship": cls.WRONG_RELATIONSHIP,
                "duplicate": cls.DUPLICATE,
                "over_merge": cls.OVER_MERGE,
                "under_merge": cls.UNDER_MERGE,
                "low_confidence": cls.LOW_CONFIDENCE,
                "schema_failure": cls.SCHEMA_FAILURE,
                "business_rule_failure": cls.BUSINESS_RULE_FAILURE,
            },
            "style": {
                "missing_entity": cls.MISSING_ENTITY,
                "hallucination": cls.HALLUCINATION,
                "wrong_style": cls.WRONG_STYLE,
                "duplicate": cls.DUPLICATE,
                "over_merge": cls.OVER_MERGE,
                "under_merge": cls.UNDER_MERGE,
                "low_confidence": cls.LOW_CONFIDENCE,
                "schema_failure": cls.SCHEMA_FAILURE,
                "business_rule_failure": cls.BUSINESS_RULE_FAILURE,
            },
        }
        return rules.get(extractor_type, {}).get(match_type, cls.MISSING_ENTITY)


@dataclass(frozen=True)
class FailureDetail:
    failure_category: FailureCategory
    extractor_type: str
    entity_id: str = ""
    expected_entity: Dict[str, Any] = field(default_factory=dict)
    actual_entity: Dict[str, Any] = field(default_factory=dict)
    similarity_score: float = 0.0
    field_mismatches: Dict[str, bool] = field(default_factory=dict)
    confidence: float = 0.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_category": self.failure_category.value,
            "extractor_type": self.extractor_type,
            "entity_id": self.entity_id,
            "similarity_score": round(self.similarity_score, 4),
            "field_mismatches": dict(self.field_mismatches),
            "confidence": round(self.confidence, 4),
            "description": self.description,
        }


@dataclass
class FailureSummary:
    total_failures: int = 0
    by_extractor: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    top_failures: List[FailureDetail] = field(default_factory=list)
    details: List[FailureDetail] = field(default_factory=list)

    def add_failure(self, failure: FailureDetail) -> None:
        self.total_failures += 1
        self.details.append(failure)
        et = failure.extractor_type
        if et not in self.by_extractor:
            self.by_extractor[et] = {}
        cat_val = failure.failure_category.value
        self.by_extractor[et][cat_val] = self.by_extractor[et].get(cat_val, 0) + 1
        self.by_category[cat_val] = self.by_category.get(cat_val, 0) + 1
        self.top_failures.append(failure)
        self.top_failures.sort(key=lambda f: f.similarity_score, reverse=False)
        self.top_failures = self.top_failures[:5]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_failures": self.total_failures,
            "by_extractor": dict(self.by_extractor),
            "by_category": dict(self.by_category),
            "top_failures": [f.to_dict() for f in self.top_failures],
        }


class RegressionStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class RegressionResult:
    extractor_type: str
    metric_name: str
    current_value: float
    baseline_value: float
    delta: float
    delta_percent: float
    status: RegressionStatus
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "baseline_value": self.baseline_value,
            "delta": round(self.delta, 4),
            "delta_percent": round(self.delta_percent, 2),
            "status": self.status.value,
            "details": dict(self.details),
        }


@dataclass
class ExtractorStatistics:
    extractor_type: str
    metric_values: Dict[str, List[float]] = field(default_factory=dict)
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    confidence: float = 0.0
    ece: float = 0.0
    top5_failure: List[str] = field(default_factory=list)
    top5_success: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "confidence": round(self.confidence, 4),
            "ece": round(self.ece, 4),
            "top5_failure": self.top5_failure,
            "top5_success": self.top5_success,
        }


@dataclass
class Suggestion:
    extractor_type: str
    metric_name: str
    current_value: float
    target_value: float
    suggestion_text: str
    failure_category: Optional[FailureCategory] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 4),
            "target_value": round(self.target_value, 4),
            "suggestion": self.suggestion_text,
            "failure_category": self.failure_category.value if self.failure_category else None,
        }


@dataclass
class SuggestionReport:
    suggestions: List[Suggestion] = field(default_factory=list)
    total_suggestions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_suggestions": self.total_suggestions,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


class TrendDirection(str, Enum):
    IMPROVING = "Improving"
    STABLE = "Stable"
    REGRESSION = "Regression"
    INSUFFICIENT_DATA = "Insufficient Data"


@dataclass(frozen=True)
class TrendResult:
    extractor_type: str
    metric_name: str
    direction: TrendDirection
    values: List[float] = field(default_factory=list)
    runs: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "direction": self.direction.value,
            "values": [round(v, 4) for v in self.values],
            "runs": self.runs,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class AnalysisReport:
    report_id: str = field(default_factory=lambda: f"analysis_{utc_now_iso()}")
    failure_summary: FailureSummary = field(default_factory=FailureSummary)
    regression_results: List[RegressionResult] = field(default_factory=list)
    suggestions: List[Suggestion] = field(default_factory=list)
    statistics: Dict[str, ExtractorStatistics] = field(default_factory=dict)
    trend_results: List[TrendResult] = field(default_factory=list)
    overall_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "failure_summary": self.failure_summary.to_dict(),
            "regression_results": [r.to_dict() for r in self.regression_results],
            "suggestions": [s.to_dict() for s in self.suggestions],
            "statistics": {k: v.to_dict() for k, v in self.statistics.items()},
            "trend_results": [t.to_dict() for t in self.trend_results],
            "overall_summary": dict(self.overall_summary),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = [
            "# Knowledge Benchmark Analysis Report",
            "",
            f"**Report ID**: `{self.report_id}`",
            "",
            "---",
            "",
            "## Failure Summary",
            "",
            f"Total Failures: {self.failure_summary.total_failures}",
            "",
            "### By Category",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ]
        for cat, count in sorted(self.failure_summary.by_category.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {count} |")
        lines.append("")

        lines.extend([
            "### Top 5 Failures",
            "",
            "| Category | Extractor | Entity ID | Similarity | Confidence |",
            "|----------|-----------|-----------|------------|------------|",
        ])
        for f in self.failure_summary.top_failures:
            lines.append(
                f"| {f.failure_category.value} | {f.extractor_type} | {f.entity_id} | {f.similarity_score:.4f} | {f.confidence:.4f} |"
            )
        lines.append("")

        if self.regression_results:
            lines.extend([
                "---",
                "",
                "## Regression Analysis",
                "",
                "| Extractor | Metric | Current | Baseline | Delta | Delta% | Status |",
                "|-----------|--------|---------|----------|-------|--------|--------|",
            ])
            for r in self.regression_results:
                lines.append(
                    f"| {r.extractor_type} | {r.metric_name} | {r.current_value:.4f} | {r.baseline_value:.4f} | {r.delta:+.4f} | {r.delta_percent:+.2f}% | {r.status.value} |"
                )
            lines.append("")

        if self.suggestions:
            lines.extend([
                "---",
                "",
                "## Improvement Suggestions",
                "",
            ])
            for idx, s in enumerate(self.suggestions, 1):
                lines.extend([
                    f"### {idx}. {s.extractor_type} — {s.metric_name}",
                    "",
                    f"**Current**: {s.current_value:.4f} | **Target**: {s.target_value:.4f}",
                    "",
                    f"> {s.suggestion_text}",
                    "",
                ])

        if self.statistics:
            lines.extend([
                "---",
                "",
                "## Per-Extractor Statistics",
                "",
            ])
            for ext_name, stats in self.statistics.items():
                lines.extend([
                    f"### {ext_name}",
                    "",
                    "| Metric | Value |",
                    "|--------|-------|",
                    f"| Precision | {stats.precision:.4f} |",
                    f"| Recall | {stats.recall:.4f} |",
                    f"| F1 Score | {stats.f1:.4f} |",
                    f"| Confidence | {stats.confidence:.4f} |",
                    f"| ECE | {stats.ece:.4f} |",
                    "",
                    "**Top 5 Failures**:",
                ])
                for f_str in stats.top5_failure:
                    lines.append(f"  - {f_str}")
                lines.append("")
                lines.append("**Top 5 Successes**:")
                for s_str in stats.top5_success:
                    lines.append(f"  - {s_str}")
                lines.append("")

        if self.trend_results:
            lines.extend([
                "---",
                "",
                "## Trend Analysis",
                "",
                "| Extractor | Metric | Direction | Values |",
                "|-----------|--------|-----------|--------|",
            ])
            for t in self.trend_results:
                vals_str = " → ".join(f"{v:.4f}" for v in t.values)
                lines.append(f"| {t.extractor_type} | {t.metric_name} | {t.direction.value} | {vals_str} |")
            lines.append("")

        if self.overall_summary:
            lines.extend([
                "---",
                "",
                "## Overall Summary",
                "",
            ])
            for key, value in self.overall_summary.items():
                lines.append(f"**{key}**: {value}")

        return "\n".join(lines)
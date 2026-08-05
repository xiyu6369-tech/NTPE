"""
Suggestion Engine (RM-5.8.4)

Generates actionable improvement suggestions from failure cases.
Analyzes per-extractor precision/recall/F1 metrics and maps failures
to concrete suggestions about knowledge package improvements.

Does NOT modify prompts. Outputs improvement suggestions only.
Offline. Deterministic. No external dependencies.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import (
    FailureCategory,
    FailureSummary,
    Suggestion,
    SuggestionReport,
)


_SUGGESTION_RULES: Dict[str, List[Dict[str, str]]] = {
    "WRONG_ALIAS": [
        {
            "condition": "missing",
            "suggestion": "Increase Alias Few-shot examples in the knowledge dataset",
        },
        {
            "condition": "partial_match",
            "suggestion": "Add name variant matching rules for Alias Merge Accuracy",
        },
    ],
    "MISSING_ENTITY": [
        {
            "condition": "context_precision",
            "suggestion": "Add Context Rule to capture boundary-aware entity detection",
        },
        {
            "condition": "default",
            "suggestion": "Increase entity-specific examples in golden dataset for better coverage",
        },
    ],
    "WRONG_SCENE_BOUNDARY": [
        {
            "condition": "default",
            "suggestion": "Add Scene Boundary markup cases with location and time_of_day anchors",
        },
    ],
    "WRONG_TIMELINE": [
        {
            "condition": "default",
            "suggestion": "Add Timeline markers with explicit temporal anchors in narrative data",
        },
    ],
    "WRONG_STYLE": [
        {
            "condition": "default",
            "suggestion": "Add Positive Pattern examples for Style Consistency improvement",
        },
    ],
    "WRONG_GLOSSARY": [
        {
            "condition": "default",
            "suggestion": "Add Context Rules for glossary term disambiguation and translation accuracy",
        },
    ],
    "DUPLICATE": [
        {
            "condition": "default",
            "suggestion": "Implement entity deduplication rules for Over Merge sensitivity",
        },
    ],
    "OVER_MERGE": [
        {
            "condition": "default",
            "suggestion": "Refine Over Merge sensitivity thresholds for entity boundary detection",
        },
    ],
    "UNDER_MERGE": [
        {
            "condition": "default",
            "suggestion": "Increase Under Merge detection sensitivity with finer boundary rules",
        },
    ],
    "LOW_CONFIDENCE": [
        {
            "condition": "default",
            "suggestion": "Increase confidence calibration with more training examples for low-confidence entities",
        },
    ],
    "SCHEMA_FAILURE": [
        {
            "condition": "default",
            "suggestion": "Validate entity schema conformance: ensure all required fields are populated",
        },
    ],
    "BUSINESS_RULE_FAILURE": [
        {
            "condition": "default",
            "suggestion": "Review business rule compliance: align entity data with business expectations",
        },
    ],
    "HALLUCINATION": [
        {
            "condition": "default",
            "suggestion": "Reduce hallucinated entities through negative sampling examples",
        },
    ],
    "WRONG_RELATIONSHIP": [
        {
            "condition": "default",
            "suggestion": "Increase relationship mapping examples between entities in golden dataset",
        },
    ],
}


class SuggestionEngine:
    """Generates actionable improvement suggestions based on failure analysis.

    Determines which extractors and characteristics need improvement based on
    failure categories and generates specific, actionable suggestions.
    """

    def __init__(self):
        self._rules = _SUGGESTION_RULES

    def generate(
        self,
        failure_summary: FailureSummary,
        per_extractor_metrics: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> List[Suggestion]:
        suggestions: List[Suggestion] = []

        top_categories = sorted(
            failure_summary.by_category.items(),
            key=lambda x: -x[1],
        )

        seen: set = set()
        for category_value, count in top_categories:
            if count == 0:
                continue
            if (category_value, category_value) in seen:
                continue
            seen.add((category_value, category_value))

            rules = self._rules.get(category_value, [])
            if not rules:
                continue

            affecting_extractors = [
                et for et, cats in failure_summary.by_extractor.items()
                if category_value in cats and cats[category_value] > 0
            ]

            for extractor_name in affecting_extractors or ["all"]:
                for rule in rules:
                    text = rule["suggestion"]
                    suggestions.append(Suggestion(
                        extractor_type=extractor_name,
                        metric_name=self._category_to_metric(category_value),
                        current_value=0.0,
                        target_value=0.85,
                        suggestion_text=text,
                        failure_category=self._str_to_category(category_value),
                    ))
                    break

        if per_extractor_metrics:
            for extractor_name, metrics in per_extractor_metrics.items():
                for metric_name, value in metrics.items():
                    if metric_name in ("precision", "recall", "f1_score"):
                        if value < 0.70:
                            suggestions.append(Suggestion(
                                extractor_type=extractor_name,
                                metric_name=metric_name,
                                current_value=round(float(value), 4),
                                target_value=0.85,
                                suggestion_text=f"Improve {extractor_name} {metric_name} from {value:.2f} to 0.85 through incremental example refinement",
                                failure_category=None,
                            ))

        return suggestions

    def generate_report(
        self,
        failure_summary: FailureSummary,
        per_extractor_metrics: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> SuggestionReport:
        suggestions = self.generate(failure_summary, per_extractor_metrics)
        return SuggestionReport(
            suggestions=suggestions,
            total_suggestions=len(suggestions),
        )

    @staticmethod
    def _category_to_metric(category_value: str) -> str:
        mapping = {
            "MISSING_ENTITY": "recall",
            "HALLUCINATION": "precision",
            "WRONG_ALIAS": "precision",
            "WRONG_RELATIONSHIP": "precision",
            "WRONG_SCENE_BOUNDARY": "recall",
            "WRONG_TIMELINE": "recall",
            "WRONG_STYLE": "precision",
            "WRONG_GLOSSARY": "precision",
            "DUPLICATE": "precision",
            "OVER_MERGE": "recall",
            "UNDER_MERGE": "precision",
            "LOW_CONFIDENCE": "ece",
            "SCHEMA_FAILURE": "schema_pass_rate",
            "BUSINESS_RULE_FAILURE": "business_rule_pass_rate",
        }
        return mapping.get(category_value, "f1_score")

    @staticmethod
    def _str_to_category(value: str) -> Optional[FailureCategory]:
        try:
            return FailureCategory(value)
        except ValueError:
            return None


def create_suggestion_engine() -> SuggestionEngine:
    return SuggestionEngine()
"""
Quality Feedback Rules (RM-5.9.2)

Rule engine that evaluates QualityDecision metrics against configurable
thresholds and produces structured feedback items.

Each rule maps a metric to a severity and produces PASS/FAIL/WARNING status.

Offline. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import (
    FeedbackSeverity,
    FeedbackRuleStatus,
    QualityFeedbackItem,
)


@dataclass
class FeedbackRule:
    rule_id: str
    metric: str
    field_key: str
    target_min: float
    target_max: float
    severity_violation: FeedbackSeverity = FeedbackSeverity.HIGH
    description_template: str = "{metric} is {current:.4f}, expected [{min:.4f}, {max:.4f}]"
    recommendation_template: str = "Adjust {metric} to be within [{min:.4f}, {max:.4f}]"

    def evaluate(self, scorecard_data: Dict[str, Any]) -> QualityFeedbackItem:
        value = self._extract_value(scorecard_data)
        if value is None:
            return QualityFeedbackItem(
                rule_id=self.rule_id,
                metric=self.metric,
                current_value=0.0,
                target_value=self.target_min,
                delta=0.0,
                status=FeedbackRuleStatus.SKIPPED,
                severity=FeedbackSeverity.INFO,
                description=f"{self.metric} value is unavailable, rule skipped",
                recommendation="",
            )

        if self.target_min <= value <= self.target_max:
            return QualityFeedbackItem(
                rule_id=self.rule_id,
                metric=self.metric,
                current_value=value,
                target_value=self.target_min,
                delta=0.0,
                status=FeedbackRuleStatus.PASS,
                severity=FeedbackSeverity.INFO,
                description=self.description_template.format(
                    metric=self.metric, current=value, min=self.target_min, max=self.target_max
                ),
                recommendation="",
            )

        delta = max(self.target_min - value, value - self.target_max, key=abs)
        status = (
            FeedbackRuleStatus.FAIL
            if self.severity_violation in (FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH)
            else FeedbackRuleStatus.WARNING
        )

        return QualityFeedbackItem(
            rule_id=self.rule_id,
            metric=self.metric,
            current_value=value,
            target_value=self.target_min,
            delta=round(delta, 4),
            status=status,
            severity=self.severity_violation,
            description=self.description_template.format(
                metric=self.metric, current=value, min=self.target_min, max=self.target_max
            ),
            recommendation=self.recommendation_template.format(
                metric=self.metric, min=self.target_min, max=self.target_max
            ),
        )

    def _extract_value(self, scorecard_data: Dict[str, Any]) -> Optional[float]:
        parts = self.field_key.split(".")
        current: Any = scorecard_data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        if isinstance(current, dict):
            return float(current.get("value", 0.0))
        try:
            return float(current)
        except (ValueError, TypeError):
            return None


BUILTIN_FEEDBACK_RULES: List[FeedbackRule] = [
    FeedbackRule(
        rule_id="FB-PRECISION-001",
        metric="precision",
        field_key="scorecard.precision",
        target_min=0.85,
        target_max=1.0,
        severity_violation=FeedbackSeverity.HIGH,
    ),
    FeedbackRule(
        rule_id="FB-RECALL-001",
        metric="recall",
        field_key="scorecard.recall",
        target_min=0.85,
        target_max=1.0,
        severity_violation=FeedbackSeverity.HIGH,
    ),
    FeedbackRule(
        rule_id="FB-F1-001",
        metric="f1",
        field_key="scorecard.f1",
        target_min=0.80,
        target_max=1.0,
        severity_violation=FeedbackSeverity.CRITICAL,
    ),
    FeedbackRule(
        rule_id="FB-ECE-001",
        metric="ece",
        field_key="scorecard.ece",
        target_min=0.0,
        target_max=0.05,
        severity_violation=FeedbackSeverity.MEDIUM,
    ),
    FeedbackRule(
        rule_id="FB-OVERALL-001",
        metric="overall_score",
        field_key="scorecard.overall_score",
        target_min=0.80,
        target_max=1.0,
        severity_violation=FeedbackSeverity.CRITICAL,
    ),
]


def create_builtin_rules() -> List[FeedbackRule]:
    return [FeedbackRule(**rule.__dict__) for rule in BUILTIN_FEEDBACK_RULES]
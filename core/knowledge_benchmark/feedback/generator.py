"""
Quality Feedback Report Generator (RM-5.9.2)

Converts a QualityDecision (RM-5.9.1) into a QualityFeedbackReport
by running the built-in feedback rules against the scorecard data.

Offline. Zero external dependencies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.knowledge_benchmark.runtime.models import QualityDecision

from .models import (
    FeedbackSeverity,
    FeedbackRuleStatus,
    QualityFeedbackItem,
    QualityFeedbackReport,
)
from .rules import FeedbackRule, create_builtin_rules


class FeedbackReportGenerator:
    """Converts QualityDecision into actionable QualityFeedbackReport."""

    def __init__(self, rules: Optional[List[FeedbackRule]] = None):
        self._rules = rules or create_builtin_rules()

    def generate(
        self,
        decision: QualityDecision,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QualityFeedbackReport:
        scorecard_data = decision.to_dict()
        scorecard_data["scorecard"] = scorecard_data.get("scorecard", {})

        items: List[QualityFeedbackItem] = []
        for rule in self._rules:
            item = rule.evaluate(scorecard_data)
            items.append(item)

        overall_severity = self._compute_overall_severity(items)
        summary = self._build_summary(items, decision)
        recommendations = self._build_recommendations(items)

        report_id = f"fb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

        return QualityFeedbackReport(
            report_id=report_id,
            source_decision_status=decision.status.value,
            source_decision_rationale="; ".join(decision.reason) if decision.reason else "No rationale provided",
            overall_severity=overall_severity,
            items=items,
            summary=summary,
            recommendations=recommendations,
            metadata=metadata or {"generator": "RM-5.9.2", "mode": "offline"},
        )

    @staticmethod
    def _compute_overall_severity(items: List[QualityFeedbackItem]) -> FeedbackSeverity:
        severity_order = [
            FeedbackSeverity.CRITICAL,
            FeedbackSeverity.HIGH,
            FeedbackSeverity.MEDIUM,
            FeedbackSeverity.LOW,
            FeedbackSeverity.INFO,
        ]
        for severity in severity_order:
            if any(
                item.severity == severity and item.status in (FeedbackRuleStatus.FAIL, FeedbackRuleStatus.WARNING)
                for item in items
            ):
                return severity
        return FeedbackSeverity.INFO

    @staticmethod
    def _build_summary(items: List[QualityFeedbackItem], decision: QualityDecision) -> List[str]:
        result: List[str] = []
        fail_count = sum(1 for i in items if i.status == FeedbackRuleStatus.FAIL)
        warn_count = sum(1 for i in items if i.status == FeedbackRuleStatus.WARNING)
        pass_count = sum(1 for i in items if i.status == FeedbackRuleStatus.PASS)
        skip_count = sum(1 for i in items if i.status == FeedbackRuleStatus.SKIPPED)

        result.append(f"Source quality decision: {decision.status.value}")
        result.append(f"Total rules evaluated: {len(items)}")
        result.append(f"Rules passed: {pass_count}")
        result.append(f"Rules failed: {fail_count}")
        result.append(f"Rules warning: {warn_count}")
        if skip_count > 0:
            result.append(f"Rules skipped: {skip_count}")

        if fail_count > 0:
            failed_metrics = [i.metric for i in items if i.status == FeedbackRuleStatus.FAIL]
            result.append(f"Failed metrics: {', '.join(failed_metrics)}")

        return result

    @staticmethod
    def _build_recommendations(items: List[QualityFeedbackItem]) -> List[str]:
        return [
            item.recommendation
            for item in items
            if item.recommendation and item.status != FeedbackRuleStatus.PASS
        ]


def create_feedback_report_generator(
    rules: Optional[List[FeedbackRule]] = None,
) -> FeedbackReportGenerator:
    return FeedbackReportGenerator(rules)
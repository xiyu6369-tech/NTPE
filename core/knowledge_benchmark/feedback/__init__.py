"""
Quality Feedback Loop Package (RM-5.9.2)

Converts QualityDecision (RM-5.9.1) into actionable QualityFeedbackReport
with structured rule evaluations, severity classifications, and recommendations.

Zero provider API calls. Zero network requests. Offline only.
Does not modify translation engine, runtime, or provider modules.
"""

from __future__ import annotations

from .models import (
    FeedbackSeverity,
    FeedbackRuleStatus,
    QualityFeedbackItem,
    QualityFeedbackReport,
)
from .rules import FeedbackRule, BUILTIN_FEEDBACK_RULES, create_builtin_rules
from .generator import FeedbackReportGenerator, create_feedback_report_generator
from .serializer import serialize_to_json, serialize_to_markdown, save_report

__all__ = [
    "FeedbackSeverity",
    "FeedbackRuleStatus",
    "QualityFeedbackItem",
    "QualityFeedbackReport",
    "FeedbackRule",
    "BUILTIN_FEEDBACK_RULES",
    "create_builtin_rules",
    "FeedbackReportGenerator",
    "create_feedback_report_generator",
    "serialize_to_json",
    "serialize_to_markdown",
    "save_report",
]
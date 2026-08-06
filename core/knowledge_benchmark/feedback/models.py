"""
Quality Feedback Report Models (RM-5.9.2)

Converts QualityDecision (RM-5.9.1) into a QualityFeedbackReport with
actionable rules, severity levels, and structured recommendations.

Zero external dependencies. Offline only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeedbackSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FeedbackRuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class QualityFeedbackItem:
    rule_id: str
    metric: str
    current_value: float
    target_value: float
    delta: float
    status: FeedbackRuleStatus = FeedbackRuleStatus.PASS
    severity: FeedbackSeverity = FeedbackSeverity.INFO
    description: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "metric": self.metric,
            "current_value": round(self.current_value, 4),
            "target_value": round(self.target_value, 4),
            "delta": round(self.delta, 4),
            "status": self.status.value,
            "severity": self.severity.value,
            "description": self.description,
            "recommendation": self.recommendation,
        }


@dataclass
class QualityFeedbackReport:
    report_id: str = ""
    generated_at: str = field(default_factory=utc_now_iso)
    source_decision_status: str = "PASS"
    source_decision_rationale: str = ""
    overall_severity: FeedbackSeverity = FeedbackSeverity.INFO
    items: List[QualityFeedbackItem] = field(default_factory=list)
    summary: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "source_decision_status": self.source_decision_status,
            "source_decision_rationale": self.source_decision_rationale,
            "overall_severity": self.overall_severity.value,
            "items": [item.to_dict() for item in self.items],
            "summary": list(self.summary),
            "recommendations": list(self.recommendations),
            "metadata": dict(self.metadata),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if i.severity == FeedbackSeverity.CRITICAL)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if i.status == FeedbackRuleStatus.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.items if i.status == FeedbackRuleStatus.WARNING)

    @property
    def pass_count(self) -> int:
        return sum(1 for i in self.items if i.status == FeedbackRuleStatus.PASS)
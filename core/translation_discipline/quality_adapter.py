from __future__ import annotations

from typing import Any, Mapping
from .feedback_adapter import AdaptiveFeedbackAdapter


class UnifiedQualityGateAdapter:
    """Annotate a copy without changing quality score or decision."""

    def __init__(self, feedback_adapter: AdaptiveFeedbackAdapter) -> None:
        self.feedback_adapter = feedback_adapter

    def adapt(self, report: Mapping[str, Any]) -> dict[str, Any]:
        adapted = dict(report)
        codes = [str(item.get("code") or item.get("type") or "") for item in report.get("merged_issues", []) if isinstance(item, Mapping)]
        rules = self.feedback_adapter.map_issue_codes(codes)
        adapted["discipline_rule_codes"] = [rule.code for rule in rules]
        adapted["discipline_issue_mappings"] = {code: rule.code for code in codes if (rule := self.feedback_adapter.map_issue_code(code))}
        return adapted

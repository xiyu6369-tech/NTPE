# =====================================================
# NTPE 1.2 Professional
# Stage-15.4 Repetition / Duplicate Content Detection
# =====================================================

from __future__ import annotations

from typing import List, Optional

from .quality_context import QualityContext
from .quality_result import QualityIssue, QualityResult, QualitySeverity
from .quality_rules import BaseQualityRule
from .repetition_detection import RepetitionDetector


class RepetitionDuplicateContentRule(BaseQualityRule):
    """Quality rule that integrates deterministic repetition detection."""

    def __init__(self, detector: Optional[RepetitionDetector] = None) -> None:
        super().__init__(
            name="repetition_duplicate_content_detection",
            category="repetition",
            severity=QualitySeverity.ERROR,
            score_penalty=0.0,
            auto_repairable=False,
        )
        self.detector = detector or RepetitionDetector()

    def evaluate(self, context: QualityContext) -> QualityResult:
        analysis = self.detector.analyze(context.translated_text)
        result = QualityResult(metrics={"repetition": analysis.to_dict()})
        for span in analysis.spans:
            severity = QualitySeverity.CRITICAL if span.severity == "critical" else QualitySeverity.WARNING
            penalty = 15.0 if severity == QualitySeverity.CRITICAL else 5.0
            result.add_issue(
                QualityIssue(
                    rule_name=self.name,
                    category="repetition",
                    severity=severity,
                    message=f"Detected {span.span_type} repeated {span.count} times.",
                    score_penalty=penalty,
                    auto_repairable=False,
                    metadata=span.to_dict(),
                )
            )
        return result


def build_repetition_rules(detector: Optional[RepetitionDetector] = None) -> List[RepetitionDuplicateContentRule]:
    return [RepetitionDuplicateContentRule(detector=detector)]

# =====================================================
# NTPE 1.2 Professional
# Stage-15.5 Formatting / Structure Integrity Engine
# =====================================================

from __future__ import annotations

from .quality_context import QualityContext
from .quality_result import QualityIssue, QualityResult, QualitySeverity
from .quality_rules import BaseQualityRule
from .structure_integrity import StructureIntegrityAnalyzer


class StructureIntegrityRule(BaseQualityRule):
    def __init__(self, analyzer: StructureIntegrityAnalyzer | None = None) -> None:
        super().__init__(
            name="formatting_structure_integrity",
            category="formatting",
            severity=QualitySeverity.ERROR,
            score_penalty=0.0,
            auto_repairable=False,
        )
        self.analyzer = analyzer or StructureIntegrityAnalyzer()

    def evaluate(self, context: QualityContext) -> QualityResult:
        analysis = self.analyzer.analyze(context.source_text, context.translated_text)
        result = QualityResult(metrics={"structure_integrity": analysis.to_dict()})
        for issue in analysis.issues:
            severity = self._map_severity(issue.severity)
            penalty = self._penalty(severity)
            result.add_issue(
                QualityIssue(
                    rule_name=self.name,
                    category=self.category,
                    severity=severity,
                    message=issue.message,
                    score_penalty=penalty,
                    auto_repairable=False,
                    metadata=issue.to_dict(),
                )
            )
        result.metrics["structure_score"] = analysis.structure_score
        result.metrics["structure_passed"] = analysis.passed
        return result

    def _map_severity(self, severity: str) -> QualitySeverity:
        lowered = severity.lower()
        if lowered == "critical":
            return QualitySeverity.CRITICAL
        if lowered == "error":
            return QualitySeverity.ERROR
        return QualitySeverity.WARNING

    def _penalty(self, severity: QualitySeverity) -> float:
        if severity == QualitySeverity.CRITICAL:
            return 35.0
        if severity == QualitySeverity.ERROR:
            return 12.0
        return 4.0


def build_structure_rules() -> list[StructureIntegrityRule]:
    return [StructureIntegrityRule()]

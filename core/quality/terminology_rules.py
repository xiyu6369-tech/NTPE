# =====================================================
# NTPE 1.2 Professional
# Stage-15.3 Terminology / Character Consistency Engine
# =====================================================

from __future__ import annotations

from typing import Any, Mapping, Optional

from .quality_context import QualityContext
from .quality_result import QualityIssue, QualityResult, QualitySeverity
from .quality_rules import BaseQualityRule
from .terminology_consistency import TerminologyConsistencyAnalyzer, TerminologyEntry


class TerminologyConsistencyRule(BaseQualityRule):
    def __init__(self, glossary: Optional[Mapping[str, Any]] = None) -> None:
        super().__init__(
            name="terminology_character_consistency",
            category="terminology",
            severity=QualitySeverity.ERROR,
            score_penalty=0.0,
            auto_repairable=False,
        )
        self.glossary = dict(glossary or {})

    def evaluate(self, context: QualityContext) -> QualityResult:
        glossary = self._resolve_glossary(context)
        if not glossary:
            return QualityResult(metrics={"terminology_entries": 0})
        analyzer = TerminologyConsistencyAnalyzer.from_glossary(glossary)
        analysis = analyzer.analyze(context.source_text, context.translated_text)
        result = QualityResult(metrics={"terminology": analysis.to_dict()})
        for issue in analysis.issues:
            severity = QualitySeverity.ERROR if issue.severity in {"error", "critical"} else QualitySeverity.WARNING
            penalty = 12.0 if severity == QualitySeverity.ERROR else 4.0
            result.add_issue(
                QualityIssue(
                    rule_name=self.name,
                    category="terminology",
                    severity=severity,
                    message=issue.message,
                    score_penalty=penalty,
                    auto_repairable=False,
                    metadata=issue.to_dict(),
                )
            )
        return result

    def _resolve_glossary(self, context: QualityContext) -> Mapping[str, Any]:
        metadata = getattr(context, "metadata", {}) or {}
        glossary = metadata.get("glossary") or metadata.get("terminology") or metadata.get("character_glossary")
        if glossary:
            return glossary
        return self.glossary


def build_terminology_rules(glossary: Optional[Mapping[str, Any]] = None) -> list[TerminologyConsistencyRule]:
    return [TerminologyConsistencyRule(glossary=glossary)]

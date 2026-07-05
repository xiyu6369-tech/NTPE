# =====================================================
# NTPE 1.2 Professional
# Stage-15.2 Translation Completeness / Missing Segment Detection
# =====================================================

from __future__ import annotations

from .completeness_analyzer import TranslationCompletenessAnalyzer
from .quality_context import QualityContext
from .quality_result import QualityIssue, QualityResult, QualitySeverity
from .quality_rules import BaseQualityRule


class MissingSegmentRule(BaseQualityRule):
    """Detect source paragraphs/sentences that have no translated counterpart."""

    def __init__(self, analyzer: TranslationCompletenessAnalyzer | None = None) -> None:
        super().__init__(
            name="missing_segment_detection",
            category="completeness",
            severity=QualitySeverity.ERROR,
            score_penalty=15.0,
            auto_repairable=False,
        )
        self.analyzer = analyzer or TranslationCompletenessAnalyzer()

    def evaluate(self, context: QualityContext) -> QualityResult:
        analysis = self.analyzer.analyze(context.source_text, context.translated_text)
        result = QualityResult(metrics={"completeness": analysis.to_dict()})
        if not analysis.missing_segments:
            return result
        for segment in analysis.missing_segments:
            result.add_issue(
                QualityIssue(
                    rule_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    message=f"Source segment {segment.index} is missing from translated text.",
                    score_penalty=self.score_penalty,
                    auto_repairable=self.auto_repairable,
                    metadata=segment.to_dict(),
                )
            )
        return result


class ShortSegmentRule(BaseQualityRule):
    """Detect translated segments that are likely summaries instead of full translations."""

    def __init__(self, analyzer: TranslationCompletenessAnalyzer | None = None) -> None:
        super().__init__(
            name="short_segment_detection",
            category="completeness",
            severity=QualitySeverity.WARNING,
            score_penalty=6.0,
            auto_repairable=False,
        )
        self.analyzer = analyzer or TranslationCompletenessAnalyzer()

    def evaluate(self, context: QualityContext) -> QualityResult:
        analysis = self.analyzer.analyze(context.source_text, context.translated_text)
        result = QualityResult(metrics={"short_segment_analysis": analysis.to_dict()})
        for segment in analysis.short_segments:
            severity = QualitySeverity.ERROR if segment.severity == "error" else self.severity
            penalty = 12.0 if severity == QualitySeverity.ERROR else self.score_penalty
            result.add_issue(
                QualityIssue(
                    rule_name=self.name,
                    category=self.category,
                    severity=severity,
                    message=f"Translated segment {segment.index} may be incomplete: {segment.reason}.",
                    score_penalty=penalty,
                    auto_repairable=self.auto_repairable,
                    metadata=segment.to_dict(),
                )
            )
        return result


class TotalCompletenessRatioRule(BaseQualityRule):
    """Detect whole-chunk translations that are too short to be complete."""

    def __init__(self, minimum_total_ratio: float = 0.15) -> None:
        super().__init__(
            name="total_completeness_ratio",
            category="completeness",
            severity=QualitySeverity.ERROR,
            score_penalty=20.0,
            auto_repairable=False,
        )
        self.minimum_total_ratio = minimum_total_ratio

    def evaluate(self, context: QualityContext) -> QualityResult:
        source_length = len((context.source_text or "").strip())
        translated_length = len((context.translated_text or "").strip())
        ratio = translated_length / max(1, source_length) if source_length else 1.0
        if source_length and ratio < self.minimum_total_ratio:
            return self.fail(
                "Translated text is too short compared with source text; missing content is likely.",
                source_length=source_length,
                translated_length=translated_length,
                total_length_ratio=ratio,
                minimum_total_ratio=self.minimum_total_ratio,
            )
        return self.pass_result(total_length_ratio=ratio)


def build_completeness_rules() -> list[BaseQualityRule]:
    analyzer = TranslationCompletenessAnalyzer()
    return [
        MissingSegmentRule(analyzer),
        ShortSegmentRule(analyzer),
        TotalCompletenessRatioRule(),
    ]

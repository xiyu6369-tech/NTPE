# =====================================================
# NTPE 1.2 Professional
# Stage-15.1 Translation Quality Engine Core
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .quality_context import QualityContext
from .quality_result import QualityIssue, QualityResult, QualitySeverity


class QualityRule(Protocol):
    name: str
    category: str
    severity: QualitySeverity
    score_penalty: float
    auto_repairable: bool

    def evaluate(self, context: QualityContext) -> QualityResult:
        ...


@dataclass
class BaseQualityRule:
    name: str
    category: str = "general"
    severity: QualitySeverity = QualitySeverity.WARNING
    score_penalty: float = 1.0
    auto_repairable: bool = False

    def fail(self, message: str, **metadata: object) -> QualityResult:
        result = QualityResult()
        result.add_issue(
            QualityIssue(
                rule_name=self.name,
                category=self.category,
                severity=self.severity,
                message=message,
                score_penalty=self.score_penalty,
                auto_repairable=self.auto_repairable,
                metadata=dict(metadata),
            )
        )
        return result

    def pass_result(self, **metrics: object) -> QualityResult:
        return QualityResult(metrics=dict(metrics))


class NonEmptyTranslationRule(BaseQualityRule):
    def __init__(self) -> None:
        super().__init__(
            name="non_empty_translation",
            category="completeness",
            severity=QualitySeverity.CRITICAL,
            score_penalty=100.0,
            auto_repairable=False,
        )

    def evaluate(self, context: QualityContext) -> QualityResult:
        if context.source_text.strip() and not context.translated_text.strip():
            return self.fail("Translated text is empty while source text is not empty.")
        return self.pass_result()


class LengthRatioRule(BaseQualityRule):
    def __init__(self, minimum_ratio: float = 0.15, maximum_ratio: float = 4.0) -> None:
        super().__init__(
            name="source_target_length_ratio",
            category="completeness",
            severity=QualitySeverity.WARNING,
            score_penalty=8.0,
            auto_repairable=False,
        )
        self.minimum_ratio = minimum_ratio
        self.maximum_ratio = maximum_ratio

    def evaluate(self, context: QualityContext) -> QualityResult:
        if context.source_length == 0:
            return self.pass_result(length_ratio=1.0)
        ratio = context.translated_length / max(1, context.source_length)
        if ratio < self.minimum_ratio or ratio > self.maximum_ratio:
            return self.fail(
                "Source/target length ratio is outside the configured bounds.",
                length_ratio=ratio,
                minimum_ratio=self.minimum_ratio,
                maximum_ratio=self.maximum_ratio,
            )
        return self.pass_result(length_ratio=ratio)


class PlaceholderIntegrityRule(BaseQualityRule):
    def __init__(self) -> None:
        super().__init__(
            name="placeholder_integrity",
            category="formatting",
            severity=QualitySeverity.ERROR,
            score_penalty=10.0,
            auto_repairable=False,
        )

    def evaluate(self, context: QualityContext) -> QualityResult:
        import re
        pattern = re.compile(r"\{[^{}]+\}|%\w|\$\{[^{}]+\}")
        src = set(pattern.findall(context.source_text or ""))
        dst = set(pattern.findall(context.translated_text or ""))
        missing = sorted(src - dst)
        if missing:
            return self.fail("Translated text is missing source placeholders.", missing_placeholders=missing)
        return self.pass_result(placeholders=len(src))


def build_default_quality_rules() -> list[QualityRule]:
    rules: list[QualityRule] = [
        NonEmptyTranslationRule(),
        LengthRatioRule(),
        PlaceholderIntegrityRule(),
    ]
    try:
        from .completeness_rules import build_completeness_rules
        rules.extend(build_completeness_rules())
    except Exception:
        # Keep Stage-15.1 imports backward-compatible even if optional
        # Stage-15.2 completeness modules are not available in legacy builds.
        pass
    try:
        from .terminology_rules import build_terminology_rules
        rules.extend(build_terminology_rules())
    except Exception:
        # Keep Stage-15.1/15.2 imports backward-compatible even if optional
        # Stage-15.3 terminology modules are not available in legacy builds.
        pass
    try:
        from .repetition_rules import build_repetition_rules
        rules.extend(build_repetition_rules())
    except Exception:
        # Keep earlier Stage-15 builds backward-compatible if Stage-15.4
        # repetition modules are not present.
        pass
    try:
        from .structure_rules import build_structure_rules
        rules.extend(build_structure_rules())
    except Exception:
        # Keep earlier Stage-15 builds backward-compatible if Stage-15.5
        # structure modules are not present.
        pass
    return rules

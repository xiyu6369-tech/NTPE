from __future__ import annotations

from .contract import QualityComponent, QualityContext, QualityResult

WEIGHTS = {"critical": 0.35, "error": 0.18, "warning": 0.06, "info": 0.0}


class QualityScorer(QualityComponent):
    name = "quality_scorer"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        score = 1.0
        for issue in result.issues:
            score -= WEIGHTS.get(issue.severity, 0.05)
        result.score = max(0.0, round(score, 3))
        result.passed = result.score >= 0.72 and not any(issue.severity in {"critical"} for issue in result.issues)
        return result

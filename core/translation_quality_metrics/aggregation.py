from __future__ import annotations

from core.translation_quality_defects import TranslationDefect, validate_defects

from .config import QualityMetricsConfig
from .dimensions import QUALITY_DIMENSIONS
from .evidence import defects_for_dimension
from .model import QualityMetric
from .scoring import score_evidence
from .weights import DIMENSION_WEIGHTS


def calculate_quality_metrics(defects: tuple[TranslationDefect, ...], config: QualityMetricsConfig | None = None) -> tuple[QualityMetric, ...]:
    config = config or QualityMetricsConfig()
    defects = validate_defects(defects)
    metrics: list[QualityMetric] = []
    for dimension in QUALITY_DIMENSIONS[:-1]:
        evidence = defects_for_dimension(dimension, defects)
        blocking = sum(1 for row in evidence if row.blocking)
        if evidence:
            score = score_evidence(evidence)
            status = "blocking" if blocking else "evaluated"
            rationale = "Score derived from human-confirmed defect severity and blocking evidence."
        else:
            score = config.neutral_score
            status = "insufficient_evidence"
            rationale = "Neutral placeholder; this dimension was not reviewed and is not treated as full score."
        metrics.append(QualityMetric(dimension, score, DIMENSION_WEIGHTS[dimension], status, tuple(row.defect_id for row in evidence), len(evidence), blocking, rationale))
    evaluated = [row for row in metrics if row.status != "insufficient_evidence"]
    total_weight = sum(row.weight for row in evaluated)
    blocking_count = sum(1 for row in defects if row.blocking)
    if not evaluated:
        metrics.append(QualityMetric("overall", config.neutral_score, 1.0, "insufficient_evidence", (), 0, 0, "Neutral placeholder; no reviewed dimensions were available for aggregation."))
        return tuple(metrics)
    overall_score = sum(row.score * row.weight for row in evaluated) / total_weight
    if blocking_count:
        overall_score = min(overall_score, config.blocking_overall_cap)
    metrics.append(QualityMetric("overall", round(overall_score, 2), 1.0, "blocking" if blocking_count else "evaluated", tuple(row.defect_id for row in defects), len(defects), blocking_count, "Weighted evaluated dimensions with a fail-closed cap for blocking defects."))
    return tuple(metrics)

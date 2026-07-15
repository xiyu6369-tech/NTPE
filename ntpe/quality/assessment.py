"""Public read-only quality assessment view."""

from __future__ import annotations

from .compatibility import defects_input, metrics_input
from .models import QualityAssessment


def assess(*, defects: object, metrics: object) -> QualityAssessment:
    defect_rows, defect_references = defects_input(defects)
    metric_rows, quality_pass, metric_references = metrics_input(metrics)
    overall = next(row for row in metric_rows if row.dimension == "overall")
    blocking = sum(1 for row in defect_rows if row.blocking)
    if overall.blocking_defect_count != blocking:
        raise ValueError("defect and metric blocking counts disagree")
    if blocking and quality_pass:
        raise ValueError("blocking evidence cannot pass quality")
    insufficient = tuple(row.dimension for row in metric_rows if row.status == "insufficient_evidence")
    return QualityAssessment(
        defects=defect_rows,
        metrics=metric_rows,
        blocking_defect_count=blocking,
        overall_score=overall.score,
        quality_pass=quality_pass,
        insufficient_evidence_dimensions=insufficient,
        source_references=defect_references + metric_references,
    )


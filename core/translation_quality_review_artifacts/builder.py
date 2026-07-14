from __future__ import annotations

import hashlib
from pathlib import Path

from core.translation_quality_defects import TranslationDefect
from core.translation_quality_metrics import QualityMetric

from .config import ReviewArtifactConfig
from .model import StructuredReview
from .validator import validate_review


def build_structured_review(source_artifact: str | Path, source_review: str | Path, defects: tuple[TranslationDefect, ...], metrics: tuple[QualityMetric, ...], config: ReviewArtifactConfig | None = None) -> StructuredReview:
    config = config or ReviewArtifactConfig()
    reviewed = tuple(row.dimension for row in metrics if row.dimension != "overall" and row.status != "insufficient_evidence")
    review = StructuredReview(config.review_id, config.source_execution_stage, hashlib.sha256(Path(source_artifact).read_bytes()).hexdigest(), hashlib.sha256(Path(source_review).read_bytes()).hexdigest(), config.review_type, config.review_origin, True, True, False, reviewed, len(defects), sum(1 for row in defects if row.blocking), True)
    return validate_review(review)

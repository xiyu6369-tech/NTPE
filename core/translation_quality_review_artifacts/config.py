from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewArtifactConfig:
    review_id: str = "TE-V71-STAGE113-REVIEW-001"
    source_execution_stage: str = "TE-v7.0-Stage10.10.1"
    review_type: str = "human_translation_quality_review"
    review_origin: str = "stage10101_review_txt"

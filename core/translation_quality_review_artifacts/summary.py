from __future__ import annotations

from .model import StructuredReview


def review_summary(review: StructuredReview) -> dict[str, object]:
    return {"review_id": review.review_id, "quality_pass": review.quality_pass, "human_review_completed": review.human_review_completed, "defect_count": review.defect_count, "blocking_defect_count": review.blocking_defect_count, "new_translation_generated": False, "provider_executed_in_this_stage": False}

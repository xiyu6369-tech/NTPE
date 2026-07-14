from __future__ import annotations

from .model import StructuredReview


def validate_review(review: StructuredReview) -> StructuredReview:
    if not review.review_id or len(review.source_artifact_sha256) != 64 or len(review.source_review_sha256) != 64:
        raise ValueError("structured review identity invalid")
    if not review.human_review_required or not review.human_review_completed:
        raise ValueError("structured review must retain completed human review evidence")
    if review.quality_pass:
        raise ValueError("known blocking review cannot pass quality")
    if not review.content_redacted or review.new_translation_generated or review.provider_executed_in_this_stage:
        raise ValueError("structured review safety boundary invalid")
    if review.defect_count < 1 or review.blocking_defect_count < 1:
        raise ValueError("structured review defect evidence invalid")
    return review

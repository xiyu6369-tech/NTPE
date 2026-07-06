# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from typing import Optional

from .review_approval_layer import ReviewApprovalLayer
from .review_gate import ApprovalGatePolicy
from .review_result import ReviewResult


def evaluate_review_gate(task_id: str, quality_score: Optional[float] = None, *, approved: bool = False) -> ReviewResult:
    layer = ReviewApprovalLayer(ApprovalGatePolicy(require_manual_approval=True))
    layer.create_task(task_id)
    if approved:
        layer.approve(task_id)
    return layer.evaluate(task_id, quality_score)

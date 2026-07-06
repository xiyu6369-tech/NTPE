# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from dataclasses import dataclass
from typing import Optional

from .review_result import ReviewResult
from .review_state import ReviewState
from .review_task import ReviewTask


@dataclass
class ApprovalGatePolicy:
    require_manual_approval: bool = True
    allow_changes_requested: bool = False
    minimum_quality_score: float = 0.0


class ApprovalGate:
    def __init__(self, policy: Optional[ApprovalGatePolicy] = None) -> None:
        self.policy = policy or ApprovalGatePolicy()

    def evaluate(self, task: ReviewTask, quality_score: Optional[float] = None) -> ReviewResult:
        if quality_score is not None and quality_score < self.policy.minimum_quality_score:
            return ReviewResult(
                approved=False,
                state=task.state,
                task_id=task.task_id,
                reason="quality_score_below_threshold",
                metadata={"quality_score": quality_score},
            )
        if task.state == ReviewState.APPROVED:
            return ReviewResult(True, task.state, task.task_id, "approved")
        if self.policy.allow_changes_requested and task.state == ReviewState.CHANGES_REQUESTED:
            return ReviewResult(True, task.state, task.task_id, "changes_requested_allowed")
        if not self.policy.require_manual_approval and task.state == ReviewState.PENDING:
            return ReviewResult(True, task.state, task.task_id, "manual_approval_not_required")
        return ReviewResult(False, task.state, task.task_id, "approval_required")

# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from typing import Optional

from .review_events import (
    REVIEW_APPROVED,
    REVIEW_CANCELLED,
    REVIEW_CHANGES_REQUESTED,
    REVIEW_CREATED,
    REVIEW_REJECTED,
    REVIEW_STARTED,
    ReviewEvent,
    ReviewEventBus,
)
from .review_gate import ApprovalGate, ApprovalGatePolicy
from .review_registry import ReviewRegistry
from .review_result import ReviewResult
from .review_task import ReviewTask


class ReviewApprovalLayer:
    def __init__(self, gate_policy: Optional[ApprovalGatePolicy] = None) -> None:
        self.registry = ReviewRegistry()
        self.events = ReviewEventBus()
        self.gate = ApprovalGate(gate_policy)

    def create_task(self, task_id: str, **kwargs) -> ReviewTask:
        task = ReviewTask(task_id=task_id, **kwargs)
        self.registry.register(task)
        self.events.emit(ReviewEvent(REVIEW_CREATED, task_id, task.to_dict()))
        return task

    def start(self, task_id: str, reviewer: Optional[str] = None) -> ReviewTask:
        task = self.registry.require(task_id).start(reviewer)
        self.events.emit(ReviewEvent(REVIEW_STARTED, task_id, task.to_dict()))
        return task

    def approve(self, task_id: str, author: str = "system", message: str = "Approved") -> ReviewTask:
        task = self.registry.require(task_id).approve(author, message)
        self.events.emit(ReviewEvent(REVIEW_APPROVED, task_id, task.to_dict()))
        return task

    def reject(self, task_id: str, author: str = "system", message: str = "Rejected") -> ReviewTask:
        task = self.registry.require(task_id).reject(author, message)
        self.events.emit(ReviewEvent(REVIEW_REJECTED, task_id, task.to_dict()))
        return task

    def request_changes(self, task_id: str, author: str = "system", message: str = "Changes requested") -> ReviewTask:
        task = self.registry.require(task_id).request_changes(author, message)
        self.events.emit(ReviewEvent(REVIEW_CHANGES_REQUESTED, task_id, task.to_dict()))
        return task

    def cancel(self, task_id: str, author: str = "system", message: str = "Cancelled") -> ReviewTask:
        task = self.registry.require(task_id).cancel(author, message)
        self.events.emit(ReviewEvent(REVIEW_CANCELLED, task_id, task.to_dict()))
        return task

    def evaluate(self, task_id: str, quality_score: Optional[float] = None) -> ReviewResult:
        return self.gate.evaluate(self.registry.require(task_id), quality_score)

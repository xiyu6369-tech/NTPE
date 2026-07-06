# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .review_exceptions import ReviewStateError
from .review_state import ReviewState


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReviewComment:
    author: str
    message: str
    created_at: str = field(default_factory=_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewTask:
    task_id: str
    workflow_id: str = ""
    target_id: str = ""
    reviewer: str = ""
    state: ReviewState = ReviewState.PENDING
    comments: List[ReviewComment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def start(self, reviewer: Optional[str] = None) -> "ReviewTask":
        if self.state.is_terminal:
            raise ReviewStateError(f"Cannot start terminal review task: {self.state.value}")
        if reviewer:
            self.reviewer = reviewer
        self.state = ReviewState.IN_REVIEW
        self.updated_at = _now()
        return self

    def add_comment(self, author: str, message: str, **metadata: Any) -> "ReviewTask":
        self.comments.append(ReviewComment(author=author, message=message, metadata=metadata))
        self.updated_at = _now()
        return self

    def approve(self, author: str = "system", message: str = "Approved") -> "ReviewTask":
        if self.state == ReviewState.CANCELLED:
            raise ReviewStateError("Cannot approve a cancelled review task")
        self.add_comment(author, message)
        self.state = ReviewState.APPROVED
        return self

    def reject(self, author: str = "system", message: str = "Rejected") -> "ReviewTask":
        if self.state == ReviewState.CANCELLED:
            raise ReviewStateError("Cannot reject a cancelled review task")
        self.add_comment(author, message)
        self.state = ReviewState.REJECTED
        return self

    def request_changes(self, author: str = "system", message: str = "Changes requested") -> "ReviewTask":
        if self.state.is_terminal:
            raise ReviewStateError(f"Cannot request changes for terminal review task: {self.state.value}")
        self.add_comment(author, message)
        self.state = ReviewState.CHANGES_REQUESTED
        return self

    def cancel(self, author: str = "system", message: str = "Cancelled") -> "ReviewTask":
        if not self.state.is_terminal:
            self.add_comment(author, message)
            self.state = ReviewState.CANCELLED
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "target_id": self.target_id,
            "reviewer": self.reviewer,
            "state": self.state.value,
            "comments": [comment.__dict__ for comment in self.comments],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

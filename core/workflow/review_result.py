# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .review_state import ReviewState


@dataclass
class ReviewResult:
    approved: bool
    state: ReviewState
    task_id: str = ""
    reason: str = ""
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "state": self.state.value,
            "task_id": self.task_id,
            "reason": self.reason,
            "comments": list(self.comments),
            "metadata": dict(self.metadata),
        }

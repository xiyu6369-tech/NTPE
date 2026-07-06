# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from typing import Dict, Iterable

from .review_state import ReviewState
from .review_task import ReviewTask


def build_review_metrics(tasks: Iterable[ReviewTask]) -> Dict[str, int]:
    metrics = {
        "total": 0,
        "pending": 0,
        "in_review": 0,
        "approved": 0,
        "rejected": 0,
        "changes_requested": 0,
        "cancelled": 0,
    }
    for task in tasks:
        metrics["total"] += 1
        metrics[task.state.value] = metrics.get(task.state.value, 0) + 1
    metrics["terminal"] = metrics["approved"] + metrics["rejected"] + metrics["cancelled"]
    return metrics

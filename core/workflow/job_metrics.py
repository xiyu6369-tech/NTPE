# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from collections.abc import Iterable

from .job_result import JobResult


def build_job_metrics(results: Iterable[JobResult], pending_count: int = 0) -> dict[str, int | float]:
    items = list(results)
    completed = sum(1 for result in items if result.status == "completed")
    failed = sum(1 for result in items if result.status == "failed")
    total = len(items) + pending_count
    return {
        "total_jobs": total,
        "completed_jobs": completed,
        "failed_jobs": failed,
        "pending_jobs": pending_count,
        "success_rate": (completed / len(items)) if items else 0.0,
    }

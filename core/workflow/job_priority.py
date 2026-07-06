# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from enum import IntEnum


class JobPriority(IntEnum):
    LOW = 30
    NORMAL = 20
    HIGH = 10
    CRITICAL = 0


def normalize_priority(priority: int | str | JobPriority | None) -> int:
    if isinstance(priority, JobPriority):
        return int(priority)
    if isinstance(priority, int):
        return priority
    if isinstance(priority, str):
        key = priority.strip().upper()
        if key in JobPriority.__members__:
            return int(JobPriority[key])
    return int(JobPriority.NORMAL)

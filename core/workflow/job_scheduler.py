# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from collections.abc import Iterable

from .job_context import JobContext
from .job_events import JOB_PAUSED, JOB_RESUMED, JobEventBus
from .job_metrics import build_job_metrics
from .job_queue import JobQueue
from .job_result import JobResult
from .job_state import JOB_FAILED
from .job_worker import JobWorker
from .workflow_engine import TranslationWorkflowEngine


class JobScheduler:
    """Stage-17.2 facade for batch workflow scheduling."""

    stage = "Stage-17.2"
    name = "Job Scheduler / Batch Task Manager"

    def __init__(self, workflow_engine: TranslationWorkflowEngine | None = None, event_bus: JobEventBus | None = None) -> None:
        self.event_bus = event_bus or JobEventBus()
        self.queue = JobQueue(self.event_bus)
        self.worker = JobWorker(workflow_engine, self.event_bus)
        self.results: list[JobResult] = []

    def submit(self, source_text: str, *, priority: int | str | None = None, metadata: dict | None = None) -> JobContext:
        return self.queue.put(JobContext(source_text=source_text, priority=priority or "normal", metadata=metadata or {}))

    def submit_many(self, source_items: Iterable[str]) -> list[JobContext]:
        return [self.submit(item) for item in source_items]

    def pause(self) -> None:
        self.queue.pause()
        self.event_bus.emit(JOB_PAUSED)

    def resume(self) -> None:
        self.queue.resume()
        self.event_bus.emit(JOB_RESUMED)

    def run_next(self) -> JobResult:
        job = self.queue.get()
        result = self.worker.run(job)
        self.results.append(result)
        return result

    def run_all(self) -> list[JobResult]:
        while not self.queue.empty():
            result = self.run_next()
            if result.status == JOB_FAILED:
                # Stage-17.2 records failure and continues; advanced retry orchestration remains extensible.
                continue
        return list(self.results)

    def metrics(self) -> dict[str, int | float]:
        return build_job_metrics(self.results, pending_count=len(self.queue))

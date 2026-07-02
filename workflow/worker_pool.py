"""Worker pool for NTPE Stage-09.4."""
from __future__ import annotations
from .worker_models import Worker, WorkerStatus

class WorkerPool:
    def __init__(self) -> None:
        self._workers: list[Worker] = []
        self._cursor = 0

    def add(self, worker: Worker) -> Worker:
        worker.mark(WorkerStatus.IDLE)
        self._workers.append(worker)
        return worker

    def acquire(self) -> Worker | None:
        if not self._workers:
            return None
        for _ in range(len(self._workers)):
            worker = self._workers[self._cursor % len(self._workers)]
            self._cursor += 1
            if worker.status in {WorkerStatus.IDLE, WorkerStatus.CREATED, WorkerStatus.STOPPED}:
                return worker
        return self._workers[0]

    def all(self) -> tuple[Worker, ...]:
        return tuple(self._workers)

    def __len__(self) -> int:
        return len(self._workers)

    def manifest(self) -> dict:
        return {"count": len(self._workers), "workers": [worker.to_dict() for worker in self._workers]}

"""Worker registry for NTPE Stage-09.4."""
from __future__ import annotations
from typing import Dict, Iterable
from .worker_models import Worker

class WorkerRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, Worker] = {}

    def register(self, worker: Worker) -> Worker:
        self._items[worker.worker_id] = worker
        return worker

    def get(self, worker_id: str) -> Worker:
        if worker_id not in self._items:
            raise KeyError(f"worker not registered: {worker_id}")
        return self._items[worker_id]

    def all(self) -> Iterable[Worker]:
        return tuple(self._items.values())

    def ids(self) -> list[str]:
        return sorted(self._items.keys())

    def manifest(self) -> dict:
        return {"count": len(self._items), "workers": self.ids()}

from __future__ import annotations

from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
from typing import Callable, Generic, List, TypeVar

T = TypeVar("T")


@dataclass(order=True)
class ScheduledExecution(Generic[T]):
    priority: int
    sequence: int
    item: T = field(compare=False)


class ExecutionScheduler(Generic[T]):
    """Deterministic scheduler abstraction for provider execution.

    Stage-14.3 exposes FIFO and priority modes without introducing background
    threads. Higher layers can still run this scheduler in worker pools later.
    """

    def __init__(self, mode: str = "fifo"):
        if mode not in {"fifo", "priority", "sequential"}:
            raise ValueError(f"unsupported scheduler mode: {mode}")
        self.mode = mode
        self._sequence = 0
        self._fifo: Queue[T] = Queue()
        self._priority: PriorityQueue[ScheduledExecution[T]] = PriorityQueue()

    def submit(self, item: T, priority: int = 0) -> None:
        if self.mode == "priority":
            self._priority.put(ScheduledExecution(-priority, self._sequence, item))
            self._sequence += 1
        else:
            self._fifo.put(item)

    def drain(self) -> List[T]:
        out: List[T] = []
        if self.mode == "priority":
            while not self._priority.empty():
                out.append(self._priority.get().item)
        else:
            while not self._fifo.empty():
                out.append(self._fifo.get())
        return out

    def run(self, item: T, fn: Callable[[T], object], priority: int = 0) -> object:
        self.submit(item, priority=priority)
        next_item = self.drain()[0]
        return fn(next_item)

    def manifest(self) -> dict[str, object]:
        return {"mode": self.mode, "queued": self._fifo.qsize() if self.mode != "priority" else self._priority.qsize()}

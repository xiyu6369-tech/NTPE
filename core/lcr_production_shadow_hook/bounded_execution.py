from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .models import HookOutcome


@dataclass(frozen=True)
class BoundedSubmission:
    status: str
    outcome: HookOutcome | None


@dataclass(frozen=True)
class ExecutorSnapshot:
    worker_count: int
    worker_daemon: bool
    queue_capacity: int
    queue_depth: int
    in_flight: bool
    accepted: int
    completed: int
    timed_out: int
    rejected_busy: int
    late_results_discarded: int


class _Task:
    def __init__(self, function: Callable[[], HookOutcome]) -> None:
        self.function = function
        self.completed = threading.Event()
        self.expired = threading.Event()
        self.outcome: HookOutcome | None = None


class BoundedShadowExecutor:
    """One lazy daemon worker, one in-flight task, and no waiting backlog."""

    def __init__(self) -> None:
        self._queue: queue.Queue[_Task] = queue.Queue(maxsize=1)
        self._slot = threading.Lock()
        self._start_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._accepted = 0
        self._completed = 0
        self._timed_out = 0
        self._rejected_busy = 0
        self._late_results_discarded = 0

    def _ensure_worker(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        with self._start_lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="ntpe-lcr-shadow-worker",
                daemon=True,
            )
            self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            task = self._queue.get()
            try:
                outcome = task.function()
                if task.expired.is_set():
                    with self._stats_lock:
                        self._late_results_discarded += 1
                else:
                    task.outcome = outcome
                    with self._stats_lock:
                        self._completed += 1
            except Exception:
                # Hook functions already convert failures to HookOutcome. This
                # final boundary prevents a worker defect from escaping.
                pass
            finally:
                task.completed.set()
                self._slot.release()
                self._queue.task_done()

    def submit(self, function: Callable[[], HookOutcome], *, wait_ms: float) -> BoundedSubmission:
        self._ensure_worker()
        if not self._slot.acquire(blocking=False):
            with self._stats_lock:
                self._rejected_busy += 1
            return BoundedSubmission("busy", None)
        task = _Task(function)
        with self._stats_lock:
            self._accepted += 1
        try:
            self._queue.put_nowait(task)
        except queue.Full:
            self._slot.release()
            with self._stats_lock:
                self._rejected_busy += 1
            return BoundedSubmission("busy", None)
        if task.completed.wait(max(0.0, wait_ms) / 1000.0):
            return BoundedSubmission("completed", task.outcome)
        task.expired.set()
        with self._stats_lock:
            self._timed_out += 1
        return BoundedSubmission("timed_out", None)

    def snapshot(self) -> ExecutorSnapshot:
        worker = self._worker
        with self._stats_lock:
            return ExecutorSnapshot(
                worker_count=int(worker is not None and worker.is_alive()),
                worker_daemon=bool(worker is not None and worker.daemon),
                queue_capacity=self._queue.maxsize,
                queue_depth=self._queue.qsize(),
                in_flight=self._slot.locked(),
                accepted=self._accepted,
                completed=self._completed,
                timed_out=self._timed_out,
                rejected_busy=self._rejected_busy,
                late_results_discarded=self._late_results_discarded,
            )

    def wait_until_idle(self, timeout_seconds: float = 1.0) -> bool:
        deadline = time.monotonic() + max(0.0, timeout_seconds)
        while self._slot.locked() and time.monotonic() < deadline:
            time.sleep(0.001)
        return not self._slot.locked()


SHADOW_EXECUTOR = BoundedShadowExecutor()


def executor_snapshot() -> ExecutorSnapshot:
    return SHADOW_EXECUTOR.snapshot()


def wait_for_shadow_idle(timeout_seconds: float = 1.0) -> bool:
    return SHADOW_EXECUTOR.wait_until_idle(timeout_seconds)

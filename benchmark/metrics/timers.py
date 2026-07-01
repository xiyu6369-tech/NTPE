from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TimerResult:
    elapsed_ms: float


class Timer:
    def __enter__(self) -> "Timer":
        self.started = time.perf_counter()
        self.ended = self.started
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.ended = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        end = getattr(self, "ended", time.perf_counter())
        return (end - self.started) * 1000.0

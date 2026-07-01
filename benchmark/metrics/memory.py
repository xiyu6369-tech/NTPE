from __future__ import annotations

import tracemalloc
from dataclasses import dataclass


@dataclass
class MemorySample:
    current_bytes: int
    peak_bytes: int


class MemorySampler:
    def __enter__(self) -> "MemorySampler":
        self._started_by_self = not tracemalloc.is_tracing()
        if self._started_by_self:
            tracemalloc.start()
        self.start_current, self.start_peak = tracemalloc.get_traced_memory()
        self.end_current = self.start_current
        self.end_peak = self.start_peak
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.end_current, self.end_peak = tracemalloc.get_traced_memory()
        if self._started_by_self:
            tracemalloc.stop()

    @property
    def delta_bytes(self) -> int:
        return int(self.end_current - self.start_current)

    @property
    def peak_bytes(self) -> int:
        return int(max(self.start_peak, self.end_peak))

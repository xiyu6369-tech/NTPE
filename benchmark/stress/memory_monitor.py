from __future__ import annotations

import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MemorySample:
    label: str
    current_bytes: int
    peak_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "current_bytes": int(self.current_bytes),
            "peak_bytes": int(self.peak_bytes),
        }


@dataclass
class MemoryMonitor:
    samples: List[MemorySample] = field(default_factory=list)
    _started_here: bool = False

    def start(self) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._started_here = True

    def sample(self, label: str = "sample") -> MemorySample:
        self.start()
        current, peak = tracemalloc.get_traced_memory()
        item = MemorySample(label=label, current_bytes=current, peak_bytes=peak)
        self.samples.append(item)
        return item

    def stop(self) -> None:
        if self._started_here and tracemalloc.is_tracing():
            tracemalloc.stop()
            self._started_here = False

    def trend(self) -> Dict[str, Any]:
        if not self.samples:
            return {"samples": 0, "current_delta_bytes": 0, "peak_bytes": 0}
        return {
            "samples": len(self.samples),
            "current_delta_bytes": self.samples[-1].current_bytes - self.samples[0].current_bytes,
            "peak_bytes": max(sample.peak_bytes for sample in self.samples),
            "points": [sample.to_dict() for sample in self.samples],
        }

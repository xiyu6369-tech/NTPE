from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass
class StressWorkload:
    """Deterministic in-memory workload used by stress and soak benchmarks."""

    name: str = "stress-workload"
    segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def size(self) -> int:
        return len(self.segments)

    def total_chars(self) -> int:
        return sum(len(str(segment.get("text", ""))) for segment in self.segments)

    def iter_segments(self) -> Iterable[Dict[str, Any]]:
        return iter(self.segments)


def generate_segments(count: int = 10, text: str = "NTPE benchmark segment") -> List[Dict[str, Any]]:
    if count < 0:
        raise ValueError("count must be >= 0")
    return [
        {
            "id": f"segment-{index + 1}",
            "index": index,
            "text": f"{text} #{index + 1}",
            "metadata": {"source": "generated"},
        }
        for index in range(count)
    ]


def generate_workload(segment_count: int = 10, text: str = "NTPE benchmark segment", name: str = "stress-workload") -> StressWorkload:
    return StressWorkload(
        name=name,
        segments=generate_segments(segment_count, text=text),
        metadata={"segment_count": segment_count, "generator": "deterministic"},
    )

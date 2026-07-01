from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class BenchmarkStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class BenchmarkResult:
    name: str
    status: BenchmarkStatus = BenchmarkStatus.PASS
    elapsed_ms: float = 0.0
    memory_delta_bytes: int = 0
    peak_memory_bytes: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def is_passed(self) -> bool:
        return self.status == BenchmarkStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "elapsed_ms": round(float(self.elapsed_ms), 6),
            "memory_delta_bytes": int(self.memory_delta_bytes),
            "peak_memory_bytes": int(self.peak_memory_bytes),
            "metrics": dict(self.metrics),
            "error": self.error,
        }

    @classmethod
    def fail(cls, name: str, error: Exception | str) -> "BenchmarkResult":
        return cls(name=name, status=BenchmarkStatus.FAIL, error=str(error))

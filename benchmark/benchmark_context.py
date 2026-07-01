from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class BenchmarkContext:
    output_dir: Path | str = "benchmark_reports"
    metadata: Dict[str, Any] = field(default_factory=dict)
    strict: bool = False

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def child(self, **metadata: Any) -> "BenchmarkContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        return BenchmarkContext(output_dir=self.output_dir, metadata=merged, strict=self.strict)

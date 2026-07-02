from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TranslateProgress:
    total: int = 0
    completed: int = 0
    skipped: int = 0
    failed: int = 0
    files: List[Dict[str, str]] = field(default_factory=list)

    def add_completed(self, source: str, output: str) -> None:
        self.completed += 1
        self.files.append({"status": "completed", "source": source, "output": output})

    def add_skipped(self, source: str, output: str, reason: str = "exists") -> None:
        self.skipped += 1
        self.files.append({"status": "skipped", "source": source, "output": output, "reason": reason})

    def add_failed(self, source: str, error: str) -> None:
        self.failed += 1
        self.files.append({"status": "failed", "source": source, "error": error})

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "total": self.total,
            "completed": self.completed,
            "skipped": self.skipped,
            "failed": self.failed,
            "files": list(self.files),
        }

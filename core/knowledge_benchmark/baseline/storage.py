"""
Baseline Storage (RM-5.8.5)

Persistent storage layer for baseline entries and index.
Reads/writes JSON to disk with file-locking safety.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import json
import os
import tempfile
import shutil

from .models import BaselineEntry, BaselineIndex, BaselineStatus


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=".json")
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)
    shutil.move(tmp_path, str(path))


class BaselineStorage:
    """Persistent storage for baseline entries and index."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("benchmarks/results/baseline")
        self.index_path = self.storage_dir / "baseline_index.json"

    def ensure(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def read_index(self) -> BaselineIndex:
        if not self.index_path.is_file():
            return BaselineIndex()

        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = []
        for e in data.get("entries", []):
            entries.append(BaselineEntry(
                baseline_id=e.get("baseline_id", ""),
                run_id=e.get("run_id", ""),
                overall_score=e.get("overall_score", 0.0),
                grade=e.get("grade", "F"),
                extractor_scores=e.get("extractor_scores", {}),
                metric_snapshots=e.get("metric_snapshots", []),
                timestamp=e.get("timestamp", ""),
                promoted_at=e.get("promoted_at", ""),
                status=BaselineStatus(e.get("status", BaselineStatus.ACTIVE.value)),
                notes=e.get("notes", ""),
                content_hash=e.get("content_hash", ""),
            ))

        index = BaselineIndex()
        index.baselines = entries
        index.active_id = data.get("active_id", "")
        index.previous_id = data.get("previous_id", "")
        return index

    def save_index(self, index: BaselineIndex) -> None:
        self.ensure()
        _atomic_write(self.index_path, index.to_json())

    def save_entry(self, entry: BaselineEntry) -> None:
        self.ensure()
        entry_path = self.storage_dir / f"{entry.baseline_id}.json"
        _atomic_write(entry_path, entry.to_json())

    def load_entry(self, baseline_id: str) -> Optional[BaselineEntry]:
        entry_path = self.storage_dir / f"{baseline_id}.json"
        if not entry_path.is_file():
            return None

        with open(entry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return BaselineEntry(
            baseline_id=data.get("baseline_id", ""),
            run_id=data.get("run_id", ""),
            overall_score=data.get("overall_score", 0.0),
            grade=data.get("grade", "F"),
            extractor_scores=data.get("extractor_scores", {}),
            metric_snapshots=data.get("metric_snapshots", []),
            timestamp=data.get("timestamp", ""),
            promoted_at=data.get("promoted_at", ""),
            status=BaselineStatus(data.get("status", BaselineStatus.ACTIVE.value)),
            notes=data.get("notes", ""),
            content_hash=data.get("content_hash", ""),
        )

    def update_entry_status(self, baseline_id: str, new_status: BaselineStatus) -> bool:
        entry_path = self.storage_dir / f"{baseline_id}.json"
        if not entry_path.is_file():
            return False

        with open(entry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["status"] = new_status.value
        _atomic_write(entry_path, json.dumps(data, indent=2, ensure_ascii=False))
        return True

    def list_all(self) -> List[BaselineEntry]:
        index = self.read_index()
        return list(index.baselines)
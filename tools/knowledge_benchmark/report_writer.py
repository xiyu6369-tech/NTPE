"""
Report Writer (RM-5.8.5)

Generates scorecard JSON files, markdown benchmark reports, and history archives.
Writes to benchmarks/results/current/ and benchmakes/results/history/ directories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import shutil
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


@dataclass
class ReportWriter:
    output_dir: Path = field(default_factory=lambda: Path("benchmarks/results/current"))
    baseline_dir: Optional[Path] = field(default_factory=lambda: Path("benchmarks/results/baseline"))
    history_dir: Optional[Path] = field(default_factory=lambda: Path("benchmarks/results/history"))

    def write_scorecard(self, extractor_name: str, data: Dict[str, Any]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"{extractor_name}_scorecard.json"
        self._write_json(path, data)
        return path

    def write_overall_scorecard(self, data: Dict[str, Any]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "overall_scorecard.json"
        self._write_json(path, data)
        return path

    def write_report(self, content: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "benchmark_report.md"
        path.write_text(content, encoding="utf-8")
        return path

    def archive_to_history(self, run_id: str) -> Optional[Path]:
        if not self.output_dir.is_dir():
            return None
        if self.history_dir is None:
            return None

        ts = run_timestamp()
        seq_dir = self.history_dir / ts if run_id else self.history_dir / f"unlabeled_{ts}"
        seq_dir.mkdir(parents=True, exist_ok=True)

        for item in self.output_dir.iterdir():
            if item.is_file():
                shutil.copy2(str(item), str(seq_dir / item.name))

        return seq_dir

    def list_history(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if self.history_dir is None or not self.history_dir.is_dir():
            return entries

        for entry in sorted(self.history_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue

            overall_path = entry / "overall_scorecard.json"
            overall_score = None
            grade = "N/A"
            run_id = "?"

            if overall_path.is_file():
                data = self._read_json(overall_path)
                overall = data.get("overall", {}).get("overall_score")
                grade = data.get("overall", {}).get("grade", "N/A")
                run_id = data.get("metadata", {}).get("benchmark_id", "?")

            entries.append({
                "directory": entry.name,
                "timestamp": entry.name,
                "run_id": run_id,
                "overall_score": overall,
                "grade": grade,
            })

        return entries

    def load_baseline(self, extractor_name: str) -> Optional[Dict[str, Any]]:
        if self.baseline_dir is None:
            return None
        path = self.baseline_dir / f"{extractor_name}_scorecard.json"
        if not path.is_file():
            return None
        return self._read_json(path)

    def load_overall_baseline(self) -> Optional[Dict[str, Any]]:
        if self.baseline_dir is None:
            return None
        path = self.baseline_dir / "overall_scorecard.json"
        if not path.is_file():
            return None
        return self._read_json(path)

    def save_current_as_baseline(self) -> None:
        if self.baseline_dir is None:
            return
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        for json_file in self.output_dir.glob("*_scorecard.json"):
            target = self.baseline_dir / json_file.name
            target.write_bytes(json_file.read_bytes())

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
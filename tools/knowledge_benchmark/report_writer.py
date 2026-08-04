"""
Report Writer (RM-5.8.3)

Generates scorecard JSON files and markdown benchmark reports.
Writes to benchmarks/results/current/ directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReportWriter:
    output_dir: Path = field(default_factory=lambda: Path("benchmarks/results/current"))
    baseline_dir: Optional[Path] = field(default_factory=lambda: Path("benchmarks/results/baseline"))

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
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

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
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
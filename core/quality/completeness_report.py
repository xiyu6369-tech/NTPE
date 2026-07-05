# =====================================================
# NTPE 1.2 Professional
# Stage-15.2 Translation Completeness / Missing Segment Detection
# =====================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .completeness_analyzer import CompletenessAnalysis


@dataclass(frozen=True)
class CompletenessReport:
    analysis: CompletenessAnalysis
    stage: str = "Stage-15.2"
    engine: str = "Translation Completeness / Missing Segment Detection"

    def to_dict(self) -> Dict[str, Any]:
        data = self.analysis.to_dict()
        data.update({"stage": self.stage, "engine": self.engine})
        return data

    def write_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def to_summary_text(self) -> str:
        metrics = self.analysis.metrics
        lines = [
            "NTPE Completeness Report",
            f"Stage: {self.stage}",
            f"Passed: {self.analysis.passed}",
            f"Source Segments: {self.analysis.source_segments}",
            f"Translated Segments: {self.analysis.translated_segments}",
            f"Missing: {metrics.get('missing_count', 0)}",
            f"Short: {metrics.get('short_count', 0)}",
            f"Coverage Ratio: {metrics.get('segment_coverage_ratio', 1.0)}",
        ]
        for seg in self.analysis.missing_segments[:10]:
            lines.append(f"- missing segment {seg.index}: {seg.source[:80]}")
        for seg in self.analysis.short_segments[:10]:
            lines.append(f"- short segment {seg.index}: ratio={seg.length_ratio:.4f}")
        return "\n".join(lines) + "\n"

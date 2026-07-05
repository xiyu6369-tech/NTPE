# =====================================================
# NTPE 1.2 Professional
# Stage-15.4 Repetition / Duplicate Content Detection
# =====================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from .repetition_detection import RepetitionAnalysis


@dataclass(frozen=True)
class RepetitionReport:
    analysis: RepetitionAnalysis

    def to_dict(self) -> Dict[str, Any]:
        return {"repetition": self.analysis.to_dict()}

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_summary_text(self) -> str:
        data = self.analysis
        lines = [
            "NTPE Stage-15.4 Repetition / Duplicate Content Report",
            f"Status: {'PASS' if data.passed else 'FAIL'}",
            f"Warnings: {data.warning_count}",
            f"Errors: {data.error_count}",
            f"Repeated character estimate: {data.metrics.get('repeated_character_estimate', 0)}",
            f"Repetition ratio: {data.metrics.get('repetition_ratio', 0)}",
        ]
        for span in data.spans[:10]:
            preview = span.text.replace("\n", " ")[:80]
            lines.append(f"- {span.severity.upper()} {span.span_type} x{span.count}: {preview}")
        return "\n".join(lines)

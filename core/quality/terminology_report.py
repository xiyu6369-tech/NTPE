# =====================================================
# NTPE 1.2 Professional
# Stage-15.3 Terminology / Character Consistency Engine
# =====================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from .terminology_consistency import TerminologyAnalysis


@dataclass(frozen=True)
class TerminologyReport:
    analysis: TerminologyAnalysis

    def to_dict(self) -> Dict[str, Any]:
        return self.analysis.to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_text(self) -> str:
        data = self.analysis
        lines = [
            "NTPE Stage-15.3 Terminology / Character Consistency Report",
            f"Status: {'PASS' if data.passed else 'WARNING/FAIL'}",
            f"Entries checked: {data.entries_checked}",
            f"Warnings: {data.warning_count}",
            f"Errors: {data.error_count}",
        ]
        for issue in data.issues:
            lines.append(f"- [{issue.severity.upper()}] {issue.entry.source} -> {issue.entry.canonical}: {issue.message}")
        return "\n".join(lines)

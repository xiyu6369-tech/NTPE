# =====================================================
# NTPE 1.2 Professional
# Stage-15.5 Formatting / Structure Integrity Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .structure_integrity import StructureAnalysis


@dataclass
class StructureIntegrityReport:
    analysis: StructureAnalysis

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": "Stage-15.5",
            "component": "Formatting / Structure Integrity Engine",
            "analysis": self.analysis.to_dict(),
        }

    def to_summary_text(self) -> str:
        return "\n".join(
            [
                "NTPE Stage-15.5 Formatting / Structure Integrity Report",
                f"Structure score: {self.analysis.structure_score:.2f}",
                f"Passed: {self.analysis.passed}",
                f"Issues: {self.analysis.issue_count}",
                f"Paragraphs: {self.analysis.source_paragraph_count} -> {self.analysis.target_paragraph_count}",
                f"Dialogue markers: {self.analysis.source_dialogue_count} -> {self.analysis.target_dialogue_count}",
            ]
        )

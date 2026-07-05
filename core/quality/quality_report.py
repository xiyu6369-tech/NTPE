# =====================================================
# NTPE 1.2 Professional
# Stage-15.1 Translation Quality Engine Core
# =====================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .quality_context import QualityContext
from .quality_result import QualityResult


@dataclass
class QualityReport:
    context: QualityContext
    result: QualityResult

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": "Stage-15.2",
            "engine": "Translation Quality Engine Core + Completeness Detection",
            "segment_id": self.context.segment_id,
            "session_id": self.context.session_id,
            "provider_name": self.context.provider_name,
            "model_name": self.context.model_name,
            "language_pair": self.context.language_pair,
            "result": self.result.to_dict(),
        }

    def write_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def to_summary_text(self) -> str:
        data = self.result.to_dict()
        lines = [
            "NTPE Translation Quality Report",
            "Stage: Stage-15.2",
            f"Status: {data['status']}",
            f"Score: {data['score']}",
            f"Issues: {len(data['issues'])}",
        ]
        for issue in data["issues"]:
            lines.append(f"- [{issue['severity']}] {issue['rule_name']}: {issue['message']}")
        return "\n".join(lines) + "\n"

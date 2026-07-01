from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
from .contract import QualityResult


@dataclass
class QualityReport:
    result: QualityResult

    def summary(self) -> Dict[str, Any]:
        return {
            "passed": self.result.passed,
            "score": self.result.score,
            "issue_count": len(self.result.issues),
            "repair_count": len(self.result.repairs),
            "issues": [issue.to_dict() for issue in self.result.issues],
        }

    def to_manifest(self) -> Dict[str, Any]:
        return {"quality": self.summary()}

# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer
# =====================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict

from .repair_result import RepairResult


@dataclass
class QualityRepairReport:
    repair_result: RepairResult

    def to_dict(self) -> Dict[str, object]:
        return self.repair_result.to_dict()

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_summary(self) -> str:
        data = self.repair_result.to_dict()
        lines = [
            "NTPE Quality Auto Repair Summary",
            f"Status: {data['status']}",
            f"Changed: {data['changed']}",
            f"Actions: {len(data['actions'])}",
        ]
        for action in self.repair_result.actions:
            lines.append(f"- {action.name}: {action.description}")
        return "\n".join(lines)

# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze Report
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseDeploymentFreezeReport:
    stage: str
    name: str
    status: str
    manifest: Dict[str, Any]
    validation: Dict[str, Any]
    checks: Dict[str, bool] = field(default_factory=dict)
    freeze_gates: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "frozen" and bool(self.checks) and all(self.checks.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "status": self.status,
            "success": self.success,
            "manifest": dict(self.manifest),
            "validation": dict(self.validation),
            "checks": dict(self.checks),
            "freeze_gates": list(self.freeze_gates),
            "notes": list(self.notes),
        }

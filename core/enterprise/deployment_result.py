# =====================================================
# NTPE 1.2 Professional
# Stage-18.1 Enterprise Deployment Foundation Result
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseDeploymentResult:
    stage: str
    name: str
    status: str
    manifest: Dict[str, Any]
    checks: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "ready" and not self.errors and all(self.checks.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "status": self.status,
            "success": self.success,
            "manifest": dict(self.manifest),
            "checks": dict(self.checks),
            "details": dict(self.details),
            "errors": list(self.errors),
        }

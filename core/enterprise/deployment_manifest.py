# =====================================================
# NTPE 1.2 Professional
# Stage-18.1 Enterprise Deployment Foundation Manifest
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseDeploymentManifest:
    """Additive deployment manifest for enterprise packaging and runtime rollout."""

    stage: str = "Stage-18.1"
    name: str = "Enterprise Deployment Foundation"
    status: str = "active"
    version: str = "1.2-professional"
    deployment_targets: List[str] = field(
        default_factory=lambda: [
            "local-workstation",
            "team-shared-runtime",
            "enterprise-controlled-host",
        ]
    )
    compatibility_contract: List[str] = field(
        default_factory=lambda: [
            "Additive deployment layer only; no existing translation runtime behavior is replaced.",
            "Foundation v1.0 remains frozen and untouched.",
            "NTPE 1.1 LTS frozen contracts remain compatible.",
            "Stage-17 production platform freeze remains valid as the deployment baseline.",
        ]
    )
    required_capabilities: List[str] = field(
        default_factory=lambda: [
            "package_inventory",
            "environment_probe",
            "deployment_plan",
            "rollback_plan",
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "deployment_targets": list(self.deployment_targets),
            "compatibility_contract": list(self.compatibility_contract),
            "required_capabilities": list(self.required_capabilities),
        }

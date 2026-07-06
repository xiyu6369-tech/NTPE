# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze
# =====================================================

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List

from core.enterprise.deployment_validation import EnterpriseDeploymentValidation

from .freeze_manifest import EnterpriseDeploymentFreezeManifest
from .freeze_report import EnterpriseDeploymentFreezeReport


class EnterpriseDeploymentFreeze:
    """Stage-18 enterprise deployment freeze coordinator.

    This component finalizes the Stage-18 deployment layer by collecting the
    Stage-18.7 readiness validation result and publishing an immutable freeze
    manifest. It is validation-only and does not modify runtime state.
    """

    stage = "Stage-18.8"
    name = "Enterprise Deployment Freeze"

    REQUIRED_MODULES = (
        "core.enterprise.deployment_foundation",
        "core.enterprise.config_center",
        "core.enterprise.deployment_profiles",
        "core.enterprise.deployment_runtime",
        "core.enterprise.deployment_orchestrator",
        "core.enterprise.deployment_validation",
        "core.enterprise.deployment_freeze",
    )

    def __init__(self, root: str | Path | None = None, validator: EnterpriseDeploymentValidation | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.validator = validator or EnterpriseDeploymentValidation(root=self.root)
        self.manifest = EnterpriseDeploymentFreezeManifest()

    def _module_checks(self) -> Dict[str, bool]:
        checks: Dict[str, bool] = {}
        for module_name in self.REQUIRED_MODULES:
            try:
                importlib.import_module(module_name)
                checks[module_name] = True
            except Exception:  # pragma: no cover - defensive freeze audit
                checks[module_name] = False
        return checks

    def _freeze_gates(self, validation_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        manifest_payload = self.manifest.to_dict()
        compatibility = manifest_payload["compatibility_rules"]
        return [
            {
                "name": "validation_ready",
                "passed": bool(validation_payload.get("success")),
                "details": {"stage": validation_payload.get("stage"), "status": validation_payload.get("status")},
            },
            {
                "name": "manifest_frozen",
                "passed": manifest_payload.get("status") == "frozen" and bool(manifest_payload.get("manifest_hash")),
                "details": {"hash": manifest_payload.get("manifest_hash")},
            },
            {
                "name": "compatibility_locked",
                "passed": all(compatibility.values()),
                "details": compatibility,
            },
            {
                "name": "stage18_modules_declared",
                "passed": len(manifest_payload.get("frozen_modules", [])) >= 7,
                "details": {"modules": manifest_payload.get("frozen_modules", [])},
            },
            {
                "name": "destructive_actions_blocked",
                "passed": compatibility.get("no_destructive_actions") is True,
                "details": {"no_destructive_actions": compatibility.get("no_destructive_actions")},
            },
        ]

    def freeze(self, profile_name: str = "local-workstation") -> EnterpriseDeploymentFreezeReport:
        validation_result = self.validator.validate(profile_name=profile_name)
        validation_payload = validation_result.to_dict()
        manifest_payload = self.manifest.to_dict()
        module_checks = self._module_checks()
        freeze_gates = self._freeze_gates(validation_payload)

        checks = {
            "validation_success": validation_result.success,
            "manifest_status": manifest_payload["status"] == "frozen",
            "manifest_hash": bool(manifest_payload["manifest_hash"]),
            "all_required_modules": all(module_checks.values()),
            "all_freeze_gates": all(gate["passed"] for gate in freeze_gates),
            "additive_contract": manifest_payload["compatibility_rules"].get("additive_updates_only") is True,
            "backward_compatible": manifest_payload["compatibility_rules"].get("backward_compatible") is True,
        }

        status = "frozen" if all(checks.values()) else "failed"
        return EnterpriseDeploymentFreezeReport(
            stage=self.stage,
            name=self.name,
            status=status,
            manifest=manifest_payload,
            validation=validation_payload,
            checks=checks,
            freeze_gates=freeze_gates,
            notes=[
                "Stage-18 enterprise deployment layer is finalized as an additive platform layer.",
                "Foundation v1.0, NTPE 1.0 Stable, and NTPE 1.1 LTS Stable remain locked.",
                "Future changes must be delivered through additive stages only.",
            ],
        )

    def audit(self, profile_name: str = "local-workstation") -> EnterpriseDeploymentFreezeReport:
        return self.freeze(profile_name=profile_name)

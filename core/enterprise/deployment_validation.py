# =====================================================
# NTPE 1.2 Professional
# Stage-18.7 Enterprise Deployment Validation
# =====================================================

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from core.enterprise.deployment_orchestrator import EnterpriseDeploymentOrchestrator


@dataclass(frozen=True)
class EnterpriseValidationGate:
    name: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class EnterpriseValidationResult:
    stage: str
    name: str
    status: str
    profile: str
    checks: Dict[str, bool] = field(default_factory=dict)
    gates: List[Dict[str, Any]] = field(default_factory=list)
    orchestration: Dict[str, Any] = field(default_factory=dict)
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
            "profile": self.profile,
            "checks": dict(self.checks),
            "gates": list(self.gates),
            "orchestration": dict(self.orchestration),
            "details": dict(self.details),
            "errors": list(self.errors),
        }


class EnterpriseDeploymentValidation:
    """Enterprise deployment validation center.

    Stage-18.7 adds standardized readiness gates above the Stage-18.5
    orchestrator. It validates deployment state only; it never deploys files,
    overwrites configuration, or modifies frozen NTPE 1.0/1.1 contracts.
    """

    stage = "Stage-18.7"
    name = "Enterprise Deployment Validation"
    BASELINE_MODULES = (
        "core.enterprise.config_center",
        "core.enterprise.deployment_profiles",
        "core.enterprise.deployment_runtime",
        "core.enterprise.deployment_orchestrator",
    )

    def __init__(self, root: str | Path | None = None, orchestrator: EnterpriseDeploymentOrchestrator | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.orchestrator = orchestrator or EnterpriseDeploymentOrchestrator(root=self.root)

    def _check_baseline_modules(self) -> tuple[bool, Dict[str, bool], List[str]]:
        checks: Dict[str, bool] = {}
        errors: List[str] = []
        for module_name in self.BASELINE_MODULES:
            try:
                importlib.import_module(module_name)
                checks[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive validation audit
                checks[module_name] = False
                errors.append(f"{module_name}: {exc}")
        return all(checks.values()), checks, errors

    def _build_gates(self, orchestration_payload: Dict[str, Any]) -> List[EnterpriseValidationGate]:
        runtime = dict(orchestration_payload.get("runtime", {}))
        orchestration = dict(orchestration_payload.get("orchestration", {}))
        checks = dict(orchestration_payload.get("checks", {}))
        details = dict(orchestration_payload.get("details", {}))
        return [
            EnterpriseValidationGate(
                "runtime_ready",
                bool(runtime.get("success")),
                {"runtime_stage": runtime.get("stage"), "status": runtime.get("status")},
            ),
            EnterpriseValidationGate(
                "orchestration_ready",
                bool(orchestration_payload.get("success")),
                {"orchestration_stage": orchestration_payload.get("stage"), "status": orchestration_payload.get("status")},
            ),
            EnterpriseValidationGate(
                "additive_mode",
                orchestration.get("mode") == "additive" and checks.get("additive_mode") is True,
                {"mode": orchestration.get("mode"), "check": checks.get("additive_mode")},
            ),
            EnterpriseValidationGate(
                "rollback_available",
                "re_run_ntpe_validation" in orchestration.get("rollback", []) and checks.get("rollback_available") is True,
                {"rollback": orchestration.get("rollback", [])},
            ),
            EnterpriseValidationGate(
                "audit_materialized",
                bool(details.get("orchestration_audit", {}).get("orchestration_hash")),
                {"audit": details.get("orchestration_audit", {})},
            ),
        ]

    def validate(self, profile_name: str = "local-workstation") -> EnterpriseValidationResult:
        checks: Dict[str, bool] = {}
        details: Dict[str, Any] = {}
        errors: List[str] = []

        modules_ok, module_details, module_errors = self._check_baseline_modules()
        checks["baseline_modules"] = modules_ok
        details["baseline_modules"] = module_details
        errors.extend(module_errors)

        orchestration_result = self.orchestrator.prepare(profile_name)
        orchestration_payload = orchestration_result.to_dict()
        gates = self._build_gates(orchestration_payload)
        gate_payload = [gate.to_dict() for gate in gates]

        checks["orchestrator_success"] = orchestration_result.success
        checks["gate_count"] = len(gates) >= 5
        checks["all_gates_passed"] = all(gate.passed for gate in gates)
        checks["profile_match"] = orchestration_payload.get("orchestration", {}).get("profile") == profile_name
        checks["validation_additive"] = orchestration_payload.get("orchestration", {}).get("mode") == "additive"

        details["validation_contract"] = {
            "mode": "readiness-validation-only",
            "frozen_layers": ["Foundation v1.0", "NTPE 1.1 LTS", "Stage-17.8"],
            "destructive_actions": False,
        }

        status = "ready" if not errors and all(checks.values()) else "failed"
        return EnterpriseValidationResult(
            stage=self.stage,
            name=self.name,
            status=status,
            profile=profile_name,
            checks=checks,
            gates=gate_payload,
            orchestration=orchestration_payload,
            details=details,
            errors=errors,
        )

    def validate_all(self, profiles: List[str] | None = None) -> Dict[str, EnterpriseValidationResult]:
        selected = profiles or ["local-workstation", "team-shared-runtime", "enterprise-controlled-host"]
        return {profile: self.validate(profile) for profile in selected}

    def audit(self, profile_name: str = "local-workstation") -> EnterpriseValidationResult:
        return self.validate(profile_name=profile_name)

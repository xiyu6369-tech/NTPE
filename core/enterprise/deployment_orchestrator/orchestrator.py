from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List

from core.enterprise.deployment_runtime import EnterpriseDeploymentRuntime

from .orchestration_audit import build_orchestration_audit
from .orchestration_plan import EnterpriseOrchestrationPlan
from .orchestration_result import EnterpriseOrchestrationResult


class EnterpriseDeploymentOrchestrator:
    """Coordinates enterprise deployment readiness across Stage-18 layers.

    The orchestrator is non-destructive. It only resolves, validates, gates, and
    audits enterprise deployment state. It does not deploy files, overwrite user
    data, or alter frozen NTPE 1.0/1.1 contracts.
    """

    stage = "Stage-18.5"
    name = "Enterprise Deployment Orchestrator"
    BASELINE_MODULES = (
        "core.enterprise.config_center",
        "core.enterprise.deployment_profiles",
        "core.enterprise.deployment_runtime",
    )

    def __init__(self, root: str | Path | None = None, runtime: EnterpriseDeploymentRuntime | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.runtime = runtime or EnterpriseDeploymentRuntime(root=self.root)

    def _check_baseline_modules(self) -> tuple[bool, Dict[str, bool], List[str]]:
        checks: Dict[str, bool] = {}
        errors: List[str] = []
        for module_name in self.BASELINE_MODULES:
            try:
                importlib.import_module(module_name)
                checks[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive audit
                checks[module_name] = False
                errors.append(f"{module_name}: {exc}")
        return all(checks.values()), checks, errors

    def build_plan(self, profile_name: str = "local-workstation") -> EnterpriseOrchestrationPlan:
        runtime_result = self.runtime.prepare(profile_name).to_dict()
        return EnterpriseOrchestrationPlan.from_runtime_payload(runtime_result)

    def prepare(self, profile_name: str = "local-workstation") -> EnterpriseOrchestrationResult:
        checks: Dict[str, bool] = {}
        details: Dict[str, Any] = {}
        errors: List[str] = []

        modules_ok, module_details, module_errors = self._check_baseline_modules()
        checks["baseline_modules"] = modules_ok
        details["baseline_modules"] = module_details
        errors.extend(module_errors)

        runtime_result = self.runtime.prepare(profile_name)
        runtime_payload = runtime_result.to_dict()
        checks["runtime_success"] = runtime_result.success
        checks["runtime_stage"] = runtime_payload.get("stage") == "Stage-18.4"
        checks["additive_mode"] = runtime_payload.get("checks", {}).get("additive_mode") is True
        checks["compatibility_contract"] = runtime_payload.get("checks", {}).get("compatibility_contract") is True

        plan = EnterpriseOrchestrationPlan.from_runtime_payload(runtime_payload)
        orchestration_payload = plan.to_dict()
        checks["orchestration_plan"] = bool(plan.phases and plan.gates and plan.rollback)
        checks["orchestration_mode"] = plan.mode == "additive"
        checks["rollback_available"] = "re_run_ntpe_validation" in plan.rollback
        checks["orchestrator_compatibility"] = plan.metadata.get("compatibility") == "orchestrator-additive-only"

        status = "ready" if not errors and all(checks.values()) else "failed"
        result = EnterpriseOrchestrationResult(
            stage=self.stage,
            name=self.name,
            status=status,
            runtime=runtime_payload,
            orchestration=orchestration_payload,
            checks=checks,
            details=details,
            errors=errors,
        )
        details["orchestration_audit"] = build_orchestration_audit(result.to_dict()).to_dict()
        return EnterpriseOrchestrationResult(
            stage=result.stage,
            name=result.name,
            status=result.status,
            runtime=result.runtime,
            orchestration=result.orchestration,
            checks=result.checks,
            details=details,
            errors=result.errors,
        )

    def audit(self, profile_name: str = "local-workstation") -> EnterpriseOrchestrationResult:
        return self.prepare(profile_name=profile_name)

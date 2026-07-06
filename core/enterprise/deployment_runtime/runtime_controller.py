from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List

from core.enterprise.deployment_profiles import DeploymentProfileResolver
from core.enterprise.deployment_profiles.profile_audit import build_profile_audit

from .runtime_audit import build_runtime_audit
from .runtime_context import EnterpriseRuntimeContext
from .runtime_plan import EnterpriseRuntimePlan
from .runtime_result import EnterpriseRuntimeResult


class EnterpriseDeploymentRuntime:
    """Enterprise deployment runtime orchestration layer.

    Stage-18.4 executes no destructive deployment actions. It prepares, validates,
    and audits runtime deployment context in an additive and backward-compatible way.
    """

    stage = "Stage-18.4"
    name = "Enterprise Deployment Runtime"
    BASELINE_MODULES = (
        "core.enterprise.deployment_foundation",
        "core.enterprise.config_center",
        "core.enterprise.deployment_profiles",
    )

    def __init__(self, root: str | Path | None = None, resolver: DeploymentProfileResolver | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.resolver = resolver or DeploymentProfileResolver()

    def _check_baseline_modules(self) -> tuple[bool, Dict[str, bool], List[str]]:
        checks: Dict[str, bool] = {}
        errors: List[str] = []
        for module_name in self.BASELINE_MODULES:
            try:
                importlib.import_module(module_name)
                checks[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive enterprise audit
                checks[module_name] = False
                errors.append(f"{module_name}: {exc}")
        return all(checks.values()), checks, errors

    def prepare_context(self, profile_name: str = "local-workstation") -> EnterpriseRuntimeContext:
        resolved = self.resolver.resolve(profile_name)
        return EnterpriseRuntimeContext.from_config(resolved, root=self.root)

    def build_plan(self, profile_name: str = "local-workstation") -> EnterpriseRuntimePlan:
        return EnterpriseRuntimePlan.from_context(self.prepare_context(profile_name))

    def prepare(self, profile_name: str = "local-workstation") -> EnterpriseRuntimeResult:
        checks: Dict[str, bool] = {}
        details: Dict[str, Any] = {}
        errors: List[str] = []

        modules_ok, module_details, module_errors = self._check_baseline_modules()
        checks["baseline_modules"] = modules_ok
        details["baseline_modules"] = module_details
        errors.extend(module_errors)

        context = self.prepare_context(profile_name)
        context_payload = context.to_dict()
        checks["runtime_context"] = bool(context.profile and context.environment and context.target)
        checks["root_available"] = context.root_path.exists()
        checks["additive_mode"] = str(context_payload.get("config", {}).get("enterprise", {}).get("deployment_mode", "additive")) == "additive"

        plan = EnterpriseRuntimePlan.from_context(context)
        plan_payload = plan.to_dict()
        checks["runtime_plan"] = bool(plan.steps and plan.rollback_steps)
        checks["compatibility_contract"] = plan.metadata.get("compatibility") == "additive-runtime-only"

        profile_audit = build_profile_audit(profile_name, context.config, validated=True).to_dict()
        details["profile_audit"] = profile_audit
        checks["profile_audit"] = bool(profile_audit.get("config_hash"))

        status = "ready" if not errors and all(checks.values()) else "failed"
        result = EnterpriseRuntimeResult(
            stage=self.stage,
            name=self.name,
            status=status,
            context=context_payload,
            plan=plan_payload,
            checks=checks,
            details=details,
            errors=errors,
        )
        details["runtime_audit"] = build_runtime_audit(result.to_dict()).to_dict()
        return EnterpriseRuntimeResult(
            stage=result.stage,
            name=result.name,
            status=result.status,
            context=result.context,
            plan=result.plan,
            checks=result.checks,
            details=details,
            errors=result.errors,
        )

    def audit(self, profile_name: str = "local-workstation") -> EnterpriseRuntimeResult:
        return self.prepare(profile_name=profile_name)

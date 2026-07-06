# =====================================================
# NTPE 1.2 Professional
# Stage-18.1 Enterprise Deployment Foundation
# =====================================================

from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .deployment_manifest import EnterpriseDeploymentManifest
from .deployment_result import EnterpriseDeploymentResult


class EnterpriseDeploymentFoundation:
    """Non-invasive enterprise deployment planning layer.

    Stage-18.1 introduces deployment readiness metadata and planning without changing
    the frozen Foundation v1.0, NTPE 1.1 LTS, or Stage-17 production runtime modules.
    """

    stage = "Stage-18.1"
    name = "Enterprise Deployment Foundation"

    BASELINE_MODULES = (
        "core.workflow.production_platform_freeze",
        "core.workflow.production_runtime_integration",
        "core.workflow.workflow_engine",
    )

    def __init__(self, root: str | Path | None = None, manifest: EnterpriseDeploymentManifest | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.manifest = manifest or EnterpriseDeploymentManifest()

    def _check_baseline_modules(self) -> tuple[bool, Dict[str, bool], List[str]]:
        checks: Dict[str, bool] = {}
        errors: List[str] = []
        for module_name in self.BASELINE_MODULES:
            try:
                importlib.import_module(module_name)
                checks[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive readiness audit
                checks[module_name] = False
                errors.append(f"{module_name}: {exc}")
        return all(checks.values()), checks, errors

    def _package_inventory(self) -> Dict[str, Any]:
        candidate_dirs = ["core", "cli", "config", "docs", "tests"]
        existing_dirs = [name for name in candidate_dirs if (self.root / name).exists()]
        return {
            "root": str(self.root),
            "existing_directories": existing_dirs,
            "has_validator": (self.root / "ntpe_validate.py").exists(),
            "has_launcher": (self.root / "launcher.py").exists(),
        }

    def _environment_probe(self) -> Dict[str, Any]:
        return {
            "python_major": sys.version_info.major,
            "python_minor": sys.version_info.minor,
            "platform": platform.system() or "unknown",
            "implementation": platform.python_implementation(),
        }

    def build_deployment_plan(self, target: str = "local-workstation") -> Dict[str, Any]:
        if target not in self.manifest.deployment_targets:
            target = "local-workstation"
        return {
            "target": target,
            "mode": "additive",
            "baseline": "Stage-17.8 Production Platform Freeze",
            "steps": [
                "verify_repository_root",
                "verify_stage17_freeze_baseline",
                "collect_package_inventory",
                "prepare_runtime_configuration",
                "preserve_existing_user_data",
                "run_ntpe_validation",
            ],
            "rollback": [
                "restore_previous_git_commit",
                "restore_previous_delta_package",
                "re-run_ntpe_validation",
            ],
        }

    def audit(self, target: str = "local-workstation") -> EnterpriseDeploymentResult:
        checks: Dict[str, bool] = {}
        details: Dict[str, Any] = {}
        errors: List[str] = []

        modules_ok, module_details, module_errors = self._check_baseline_modules()
        checks["baseline_modules"] = modules_ok
        details["baseline_modules"] = module_details
        errors.extend(module_errors)

        inventory = self._package_inventory()
        checks["package_inventory"] = bool(inventory["existing_directories"] and inventory["has_validator"])
        details["package_inventory"] = inventory

        environment = self._environment_probe()
        checks["environment_probe"] = environment["python_major"] >= 3
        details["environment_probe"] = environment

        plan = self.build_deployment_plan(target)
        checks["deployment_plan"] = bool(plan["steps"] and plan["rollback"])
        details["deployment_plan"] = plan

        manifest = self.manifest.to_dict()
        checks["compatibility_contract"] = bool(manifest.get("compatibility_contract"))
        checks["required_capabilities"] = set(manifest.get("required_capabilities", [])) <= set(checks.keys()) | {"rollback_plan"}

        status = "ready" if not errors and all(checks.values()) else "failed"
        return EnterpriseDeploymentResult(
            stage=self.stage,
            name=self.name,
            status=status,
            manifest=manifest,
            checks=checks,
            details=details,
            errors=errors,
        )

    def prepare(self, target: str = "local-workstation") -> EnterpriseDeploymentResult:
        return self.audit(target=target)

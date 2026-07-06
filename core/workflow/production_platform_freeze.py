# =====================================================
# NTPE 1.2 Professional
# Stage-17.8 Production Platform Freeze
# =====================================================

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

from .platform_freeze_manifest import ProductionPlatformFreezeManifest
from .platform_freeze_result import ProductionPlatformFreezeResult


class ProductionPlatformFreeze:
    """Stage-17 production platform freeze verifier.

    This class performs a non-invasive freeze audit. It imports the Stage-17 production
    modules, validates that the production runtime can still execute, and returns a
    manifest-backed frozen result.
    """

    stage = "Stage-17.8"
    name = "Production Platform Freeze"

    REQUIRED_MODULES = (
        "core.workflow.workflow_engine",
        "core.workflow.job_scheduler",
        "core.workflow.resource_optimizer",
        "core.workflow.review_approval_layer",
        "core.workflow.export_engine",
        "core.workflow.dashboard_api",
        "core.workflow.production_runtime_integration",
    )

    def __init__(self, manifest: ProductionPlatformFreezeManifest | None = None) -> None:
        self.manifest = manifest or ProductionPlatformFreezeManifest()

    def _check_required_modules(self) -> tuple[bool, Dict[str, bool], list[str]]:
        module_checks: Dict[str, bool] = {}
        errors: list[str] = []
        for module_name in self.REQUIRED_MODULES:
            try:
                import_module(module_name)
                module_checks[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive compatibility audit
                module_checks[module_name] = False
                errors.append(f"{module_name}: {exc}")
        return all(module_checks.values()), module_checks, errors

    def _check_runtime_execution(self) -> tuple[bool, Dict[str, Any], list[str]]:
        try:
            from .production_runtime_integration import ProductionRuntimeIntegration

            result = ProductionRuntimeIntegration().run("NTPE production platform freeze probe")
            details = {
                "runtime_status": result.status,
                "runtime_success": result.success,
                "workflow_id": result.workflow_id,
                "artifact_keys": sorted(result.artifacts.keys()),
                "event_count": len(result.events),
            }
            return bool(result.success), details, list(result.errors)
        except Exception as exc:  # pragma: no cover - defensive compatibility audit
            return False, {"runtime_status": "failed"}, [str(exc)]

    def audit(self) -> ProductionPlatformFreezeResult:
        checks: Dict[str, bool] = {}
        details: Dict[str, Any] = {}
        errors: list[str] = []

        modules_ok, module_checks, module_errors = self._check_required_modules()
        checks["required_modules"] = modules_ok
        details["required_modules"] = module_checks
        errors.extend(module_errors)

        runtime_ok, runtime_details, runtime_errors = self._check_runtime_execution()
        checks["runtime_execution"] = runtime_ok
        details["runtime_execution"] = runtime_details
        errors.extend(runtime_errors)

        checks["manifest_status"] = self.manifest.status == "frozen"
        checks["compatibility_contract"] = bool(self.manifest.compatibility_contract)

        status = "frozen" if not errors and all(checks.values()) else "failed"
        return ProductionPlatformFreezeResult(
            stage=self.stage,
            name=self.name,
            status=status,
            manifest=self.manifest.to_dict(),
            checks=checks,
            details=details,
            errors=errors,
        )

    def freeze(self) -> ProductionPlatformFreezeResult:
        return self.audit()
